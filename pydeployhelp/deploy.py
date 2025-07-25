#!/usr/bin/env python
import io
import os
import shutil
import subprocess
import time
import typing as t
from pathlib import Path
from typing import Annotated

import typer
from dotenv import dotenv_values
from jinja2 import Template
from ruamel.yaml import YAML

from pydeployhelp import __version__
from pydeployhelp.base import CLIBase, Configs


class Deploy(CLIBase):
    def __init__(
        self,
        tasks: list[str] | None = None,
        targets: list[str] | None = None,
        deploydir: str = "deploy",
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tasks = tasks
        self.targets = targets
        self.deploydir = Path(deploydir)

    def validate_docker_binaries(self) -> None:
        """Check that all required binaries exist and are accessible by current user"""

        try:
            # Run the command while suppressing stdout and stderr
            with Path(os.devnull).open("w") as devnull:
                docker_path = shutil.which("docker")
                if docker_path is None:
                    raise FileNotFoundError("'docker' executable not found in PATH")

                subprocess.run([docker_path, "version"], stdout=devnull, stderr=devnull, check=True)  # noqa: S603
        except subprocess.CalledProcessError:
            self._print_service_message(
                "Error: 'docker' command is not available or not working correctly. Is the docker daemon running?",
                color=typer.colors.RED,
            )
            raise typer.Abort from None

    def start(self) -> None:
        """Controller for all operations performed by `pydeployhelp`"""

        start_time = time.perf_counter()
        self._print_service_message("Started deploy\n", color=typer.colors.GREEN, bold=True)

        try:
            self.validate_docker_binaries()

            configs = self.load_configs(f"{self.deploydir}/config.yml")
            environ = self.load_environ(configs.context.get("env_file", ".env"))
            compose = self.load_compose(
                configs.context.get("compose", f"{self.deploydir}/docker-compose-template.j2"), environ=environ
            )
            deploy_tasks = self.enter_deploy_tasks(configs)
            deploy_targets = self.enter_deploy_targets(compose)

            if deploy_tasks != self.tasks or deploy_targets != self.targets:
                self.ask_to_continue()
        except (KeyboardInterrupt, InterruptedError, RuntimeError):
            self._print_service_message("\nFinished deploy", color=typer.colors.RED, bold=True)
        else:
            compose_path = self.save_environment_compose(compose, deploy_targets, environ["env"])
            self.execute_pipeline(configs, environ, deploy_tasks)
            self._remove_file(compose_path)
            self._print_service_message(
                f"\nFinished deploy. Processing time: {time.perf_counter() - start_time:.1f}s",
                color=typer.colors.GREEN,
                bold=True,
            )

    def load_configs(self, path: str | Path) -> Configs:
        """Load deploy configs"""

        configs = Configs()

        path = Path(path)
        if not path.exists():
            self._print_service_message("Config file was not found, skipping", color=typer.colors.YELLOW)
        else:
            with path.open("r", encoding="utf-8") as fp:
                configs_raw = YAML().load(fp)
                configs.context.update(configs_raw.get("context", {}))
                configs.tasks.update(configs_raw.get("tasks", {}))

        if not configs.tasks:
            self._print_service_message("No tasks were found in configs", color=typer.colors.RED)
            raise typer.Abort

        return configs

    def load_environ(self, env_file: str | Path) -> dict[str, t.Any]:
        """Load environment variables from .env files (if exists)"""

        environ = {}

        env_file = Path(env_file)
        if not env_file.exists():
            self._print_service_message(".env file was not found, skipping", color=typer.colors.YELLOW)
        else:
            environ.update(dotenv_values(env_file))

        environ["env"] = environ.get("ENV", "latest")
        return environ

    def load_compose(self, path: str | Path, environ: dict[str, t.Any]) -> dict[str, t.Any]:
        """Load docker-compose data"""

        compose = {}

        path = Path(path)
        if not path.exists():
            self._print_service_message("compose file was not found, skipping", color=typer.colors.YELLOW)
        else:
            with path.open("r", encoding="utf-8") as fp:
                compose = YAML().load(io.StringIO(Template(fp.read()).render(**environ)))

        if not compose.get("services"):
            self._print_service_message("No services were found in docker-compose", color=typer.colors.RED)
            raise InterruptedError

        return compose

    def enter_deploy_tasks(self, configs: Configs) -> list[str]:
        """Receive deploy tasks names from user input"""

        allowed_tasks = list(configs.tasks)
        extended_allowed_tasks = [*allowed_tasks, "all"]

        if self.tasks and all(el in extended_allowed_tasks for el in self.tasks):
            return self.tasks

        return self.enter(allowed_items=allowed_tasks, default=allowed_tasks[0], items_name="deploy tasks")

    def enter_deploy_targets(self, compose: dict[str, t.Any]) -> list[str]:
        """Receive deploy targets names from user input"""

        allowed_targets = list(compose["services"])
        extended_allowed_tasks = [*allowed_targets, "all"]

        if self.targets and all(el in extended_allowed_tasks for el in self.targets):
            return self.targets

        return self.enter(allowed_items=allowed_targets, default="all", items_name="deploy targets")

    def save_environment_compose(self, compose: dict[str, t.Any], deploy_targets: list[str], env: str) -> Path:
        """Filter docker-compose services according to `deploy_targets`,
        rename main components according to `env` and save to new file"""

        # remove ignored services
        services = {}
        for service_name, service_data in compose["services"].items():
            if service_name not in deploy_targets:
                continue
            for ref_name in ["depends_on", "links"]:
                ref_data = service_data.get(ref_name)
                if not ref_data:
                    continue
                service_data[ref_name] = [ref for ref in ref_data if ref in deploy_targets]
            services[service_name] = service_data
        compose["services"] = services

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        compose_path = Path(f"{self.deploydir}/docker-compose-{env}.yml")
        with compose_path.open("w", encoding="utf-8") as fp:
            yaml.dump(compose, fp)
        self._add_permissions(compose_path)
        return compose_path

    def execute_pipeline(self, configs: Configs, environ: dict[str, t.Any], deploy_tasks: list[str]) -> None:
        """Execute commands from configs pipeline"""

        for task in deploy_tasks:
            for subtask in configs.tasks[task]:
                subtask_name = f"{task}/{subtask['title']}"
                self._print_service_message(f'Task "{subtask_name}": Started')
                try:
                    for i, pipe in enumerate(subtask["pipeline"]):
                        command = pipe.format(**environ)
                        typer.echo(f"Step {i + 1}: {command}\n")
                        os.system(command)  # noqa: S605
                except Exception as e:
                    self._print_service_message(f'Task "{subtask_name}": Skipping. {e}', color=typer.colors.YELLOW)
                else:
                    self._print_service_message(f'Task "{subtask_name}": Finished')


def main(
    task: Annotated[list[str] | None, typer.Option(help="List of deployment tasks defined in config.yaml")] = None,
    target: Annotated[list[str] | None, typer.Option(help="List of deployment targets defined in config.yaml")] = None,
    deploydir: Annotated[
        str,
        typer.Option(help="Path to directory with deploy scripts (normally generated via `pydeployhelp-quickstart`)"),
    ] = "deploy",
    silent: Annotated[bool, typer.Option(help="Ignore all communication with user and use default values")] = False,
    version: Annotated[bool, typer.Option(help="Print version and exit")] = False,
) -> None:
    """Main entrypoint, which will be called when executing `pydeployhelp` in console"""

    if version:
        typer.echo(f"pydeployhelp version {__version__}")
    else:
        deploy = Deploy(tasks=task or [], targets=target or [], deploydir=deploydir, silent=silent)
        deploy.start()


def run() -> None:
    typer.run(main)


if __name__ == "__main__":
    run()
