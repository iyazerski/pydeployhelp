#!/usr/bin/env python
import argparse
import os
import io
import time
from pathlib import Path
from typing import List, Set, Dict, Union

from jinja2 import Template
from ruamel.yaml import YAML

from pydeployhelp import __version__
from pydeployhelp.base import ABC, Configs
from pydeployhelp.utils import read_env_file


class Deploy(ABC):
    def __init__(self, deploydir: str = 'deploy', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deploydir = Path(deploydir)

    def validate_docker_binaries(self):
        for binary in ['docker', 'docker-compose']:
            return_code = os.system(f'{binary} -v')
            if return_code != 0:
                raise InterruptedError

    def start(self):
        start_time = time.perf_counter()
        self._print_service_message('Started deploy')

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
            self._print_service_message('Interrupted', error=True)
        else:
            compose_path = self.save_environment_compose(compose, deploy_targets, environ['env'])
            self.execute_pipeline(configs, environ, deploy_tasks)
            self._remove_file(compose_path)
            self._print_service_message(f'Finished deploy. Processing time: {time.perf_counter() - start_time:.1f}s')

    def load_configs(self, path: Union[str, Path]) -> Configs:
        """ Load deploy configs """

        configs = Configs()

        path = Path(path)
        if not path.exists():
            self._print_service_message('Config file was not found, skipping', warning=True)
        else:
            with path.open('r', encoding='utf-8') as fp:
                configs_raw = YAML().load(fp)
                configs.context.update(configs_raw.get('context', {}))
                configs.tasks.update(configs_raw.get('tasks', {}))

        if not configs.tasks:
            self._print_service_message('No tasks were found in configs', error=True)
            raise InterruptedError

        return configs

    def load_environ(self, env_file: Union[str, Path]) -> Dict:
        """ Load environment variables from .env files (if exists) """

        environ = {}

        env_file = Path(env_file)
        if not env_file.exists():
            self._print_service_message('.env file was not found, skipping', warning=True)
        else:
            environ.update(read_env_file(env_file))

        environ['env'] = environ.get('ENV', 'latest')
        return environ

    def load_compose(self, path: Union[str, Path], environ: Dict) -> Dict:
        """ Load docker-compose data """

        compose = {}

        path = Path(path)
        if not path.exists():
            self._print_service_message('compose file was not found, skipping', warning=True)
        else:
            with path.open('r', encoding='utf-8') as fp:
                compose = YAML().load(io.StringIO(Template(fp.read()).render(**environ)))

        if not compose.get('services'):
            self._print_service_message('No services were found in docker-compose', error=True)
            raise InterruptedError

        return compose

    def enter_deploy_tasks(self, configs: Configs) -> List[str]:
        """ Receive deploy tasks names from user input """

        allowed_tasks = list(configs.tasks)
        return self.enter(allowed_items=allowed_tasks, default=allowed_tasks[0], items_name='deploy tasks')

    def enter_deploy_targets(self, compose: Dict) -> Set[str]:
        """ Receive deploy targets names from user input """

        allowed_targets = list(compose['services'])
        return self.enter(allowed_items=allowed_targets, default='all', items_name='deploy targets')

    def save_environment_compose(self, compose: Dict, deploy_targets: Set[str], env: str) -> Path:
        """ Filter docker-compose services according to `deploy_targets`,
            rename main components according to `env` and save to new file
        """

        # remove ignored services, format names and links
        compose['services'] = {name: data for name, data in compose['services'].items() if name in deploy_targets}

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        compose_path = Path(f'{self.deploydir}/docker-compose-{env}.yml')
        with compose_path.open('w', encoding='utf-8') as fp:
            yaml.dump(compose, fp)
        self._add_permissions(compose_path)
        return compose_path

    def execute_pipeline(self, configs: Configs, environ: Dict, deploy_tasks: List[str]):
        """ Execute commands from configs pipeline """

        for task in deploy_tasks:
            self._print_service_message(f'Task "{task}": Started')
            for subtask in configs.tasks[task]:
                subtask_name = f'{task}/{subtask["title"]}'
                self._print_service_message(f'Subtask "{subtask_name}": Started')
                try:
                    for i, pipe in enumerate(subtask['pipeline']):
                        command = pipe.format(**environ)
                        print(f'Step {i + 1}: {command}\n')
                        os.system(command)
                except Exception as e:
                    self._print_service_message(f'Subtask "{subtask_name}": Skipping. {e}', error=True)
                else:
                    self._print_service_message(f'Subtask "{subtask_name}": Finished')
            self._print_service_message(f'Task "{task}": Finished')


def parse_args() -> argparse.ArgumentParser:
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
    args = parse_args()
    if args.version:
        print(f'pydeployhelp version {__version__}')
    else:
        deploy = Deploy(deploydir=args.deploydir, silent=args.silent)
        deploy.start()


if __name__ == "__main__":
    main()
