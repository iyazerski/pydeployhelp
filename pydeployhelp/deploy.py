#!/usr/bin/env python
import argparse
import io
import os
import time
from pathlib import Path
from typing import List, Dict, Union

from jinja2 import Template
from ruamel.yaml import YAML

from pydeployhelp import __version__
from pydeployhelp.base import ABC, Configs
from pydeployhelp.utils import read_env_file


class Deploy(ABC):
    def __init__(self, deploydir: str = 'deploy', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deploydir = Path(deploydir)
        self.docker_compose_v2_exit_code = 4096

    def validate_docker_binaries(self):
        """ Check that all required binaries exist and are accessible by current user """

        for binary in ['docker', 'docker-compose']:
            return_code = os.system(f'{binary} -v')
            if return_code == self.docker_compose_v2_exit_code:
                self._print_service_message(
                    'Seems that Docker Compose v2 is enabled. Please disable it '
                    'via `docker-compose disable-v2` and try again',
                    color=self.colors.yellow
                )
            if return_code != 0:
                raise InterruptedError

    def start(self):
        """ Controller for all operations performed by `pydeployhelp` """

        start_time = time.perf_counter()
        self._print_service_message('Started deploy\n', color=self.colors.green)

        try:
            self.validate_docker_binaries()

            configs = self.load_configs(f'{self.deploydir}/config.yml')
            environ = self.load_environ(configs.context.get('env_file', '.env'))
            compose = self.load_compose(
                configs.context.get('compose', f'{self.deploydir}/docker-compose-template.j2'), environ=environ
            )
            deploy_tasks = self.enter_deploy_tasks(configs)
            deploy_targets = self.enter_deploy_targets(compose)

            self.ask_to_continue()
        except (KeyboardInterrupt, InterruptedError):
            self._print_service_message('\nFinished deploy', color=self.colors.red)
        else:
            compose_path = self.save_environment_compose(compose, deploy_targets, environ['env'])
            self.execute_pipeline(configs, environ, deploy_tasks)
            self._remove_file(compose_path)
            self._print_service_message(
                f'\nFinished deploy. Processing time: {time.perf_counter() - start_time:.1f}s',
                color=self.colors.green
            )

    def load_configs(self, path: Union[str, Path]) -> Configs:
        """ Load deploy configs """

        configs = Configs()

        path = Path(path)
        if not path.exists():
            self._print_service_message('Config file was not found, skipping', color=self.colors.yellow)
        else:
            with path.open('r', encoding='utf-8') as fp:
                configs_raw = YAML().load(fp)
                configs.context.update(configs_raw.get('context', {}))
                configs.tasks.update(configs_raw.get('tasks', {}))

        if not configs.tasks:
            self._print_service_message('No tasks were found in configs', color=self.colors.red)
            raise InterruptedError

        return configs

    def load_environ(self, env_file: Union[str, Path]) -> Dict:
        """ Load environment variables from .env files (if exists) """

        environ = {}

        env_file = Path(env_file)
        if not env_file.exists():
            self._print_service_message('.env file was not found, skipping', color=self.colors.yellow)
        else:
            environ.update(read_env_file(env_file))

        environ['env'] = environ.get('ENV', 'latest')
        return environ

    def load_compose(self, path: Union[str, Path], environ: Dict) -> Dict:
        """ Load docker-compose data """

        compose = {}

        path = Path(path)
        if not path.exists():
            self._print_service_message('compose file was not found, skipping', color=self.colors.yellow)
        else:
            with path.open('r', encoding='utf-8') as fp:
                compose = YAML().load(io.StringIO(Template(fp.read()).render(**environ)))

        if not compose.get('services'):
            self._print_service_message('No services were found in docker-compose', color=self.colors.red)
            raise InterruptedError

        return compose

    def enter_deploy_tasks(self, configs: Configs) -> List[str]:
        """ Receive deploy tasks names from user input """

        allowed_tasks = list(configs.tasks)
        return self.enter(allowed_items=allowed_tasks, default=allowed_tasks[0], items_name='deploy tasks')

    def enter_deploy_targets(self, compose: Dict) -> List[str]:
        """ Receive deploy targets names from user input """

        allowed_targets = list(compose['services'])
        return self.enter(allowed_items=allowed_targets, default='all', items_name='deploy targets')

    def save_environment_compose(self, compose: Dict, deploy_targets: List[str], env: str) -> Path:
        """ Filter docker-compose services according to `deploy_targets`,
        rename main components according to `env` and save to new file """

        # remove ignored services
        services = {}
        for service_name, service_data in compose['services'].items():
            if service_name not in deploy_targets:
                continue
            for ref_name in ['depends_on', 'links']:
                ref_data = service_data.get(ref_name)
                if not ref_data:
                    continue
                service_data[ref_name] = [ref for ref in ref_data if ref in deploy_targets]
            services[service_name] = service_data
        compose['services'] = services

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        compose_path = Path(f'{self.deploydir}/docker-compose-{env}.yml')
        with compose_path.open('w', encoding='utf-8') as fp:
            yaml.dump(compose, fp)
        self._add_permissions(compose_path)
        return compose_path

    def execute_pipeline(self, configs: Configs, environ: Dict, deploy_tasks: List[str]) -> None:
        """ Execute commands from configs pipeline """

        for task in deploy_tasks:
            for subtask in configs.tasks[task]:
                subtask_name = f'{task}/{subtask["title"]}'
                self._print_service_message(f'Task "{subtask_name}": Started')
                try:
                    for i, pipe in enumerate(subtask['pipeline']):
                        command = pipe.format(**environ)
                        print(f'Step {i + 1}: {command}\n')
                        os.system(command)
                except Exception as e:
                    self._print_service_message(f'Task "{subtask_name}": Skipping. {e}', color=self.colors.yellow)
                else:
                    self._print_service_message(f'Task "{subtask_name}": Finished')


def parse_args() -> argparse.Namespace:
    """ Create stdin arguments parser and parse args from user input """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--deploydir',
        default='deploy',
        help='Path to directory with deploy scripts (normally generated via `pydeployhelp-quickstart`)'
    )
    parser.add_argument(
        '-s', '--silent',
        action='store_true',
        help='If specified, all communication with user will be ignored, default values will be used instead'
    )
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Print version and exit'
    )
    return parser.parse_args()


def main():
    """ Main entrypoint, which will be called when executing `pydeployhelp` in console """

    args = parse_args()
    if args.version:
        print(f'pydeployhelp version {__version__}')
    else:
        deploy = Deploy(deploydir=args.deploydir, silent=args.silent)
        deploy.start()


if __name__ == '__main__':
    main()
