#!/usr/bin/env python
import argparse
import os
import time
from pathlib import Path
from typing import List, Set, Dict, Union

from pydantic import BaseModel
from ruamel.yaml import YAML

from pydeployhelp.base import ABC, Configs
from pydeployhelp.utils import read_env_file


class Deploy(ABC):
    def __init__(self, deploydir: str = 'deploy', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deploydir = Path(deploydir)

    def start(self):
        start_time = time.perf_counter()
        self._print_service_message('Started deploy')

        try:
            configs = self.load_configs(f'{self.deploydir}/config.yml')
            environ = self.load_environ(configs.context.get('env_file', '.env'))
            compose = self.load_compose(configs.context.get('compose', f'{self.deploydir}/docker-compose.yml'))
            deploy_tasks = self.enter_deploy_tasks(configs)
            deploy_targets = self.enter_deploy_targets(compose)
        except (KeyboardInterrupt, InterruptedError):
            self._print_service_message('Interrupted', error=True)
        else:
            self.save_environment_compose(compose, deploy_targets, environ['env'])
            self.execute_pipeline(configs, environ, deploy_tasks)
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

    def load_compose(self, path: Union[str, Path]) -> Dict:
        """ Load docker-compose data """

        compose = {}

        path = Path(path)
        if not path.exists():
            self._print_service_message('compose file was not found, skipping', warning=True)
        else:
            with path.open('r', encoding='utf-8') as fp:
                compose = YAML().load(fp)

        if not compose.get('services'):
            self._print_service_message('No services were found in docker-compose', error=True)
            raise InterruptedError

        return compose

    def enter_deploy_tasks(self, configs: Configs) -> List[str]:
        """ Receive deploy tasks names from user input """

        deploy_tasks = list(configs.tasks)
        defaults = ','.join(deploy_tasks)
        if not self.silent:
            deploy_tasks = list(filter(
                lambda x: x in deploy_tasks,
                [task.strip().lower() for task in input(
                    f'Enter comma separated deploy tasks names from following: {self._format_defaults(defaults)} '
                    f'[{deploy_tasks[0]}]: ').strip().split(',')]
            )) or [deploy_tasks[0]]
        return deploy_tasks

    def enter_deploy_targets(self, compose: Dict) -> Set[str]:
        """ Receive deploy targets names from user input """

        deploy_targets = list(compose['services'])
        defaults = ','.join(deploy_targets)
        if not self.silent:
            deploy_targets = set(filter(
                lambda x: x in deploy_targets,
                (task.strip().lower() for task in input(
                    f'Enter comma separated deploy targets names from following: {self._format_defaults(defaults)} '
                    f'[{defaults}]: ').strip().split(','))
            )) or deploy_targets
        return deploy_targets

    def save_environment_compose(self, compose: Dict, deploy_targets: Set[str], env: str):
        """ Filter docker-compose services according to `deploy_targets`,
            rename main components according to `env` and save to new file
        """

        # remove ignored services, format names and links
        services = {}
        for service_name, service_data in compose['services'].items():
            if service_name not in deploy_targets:
                continue
            for special_field in ['depends_on', 'links']:
                if special_field not in service_data:
                    continue
                service_data[special_field] = [
                    f'{service}-{env}' for service in service_data[special_field] if service in deploy_targets
                ]
            services[f'{service_name}-{env}'] = service_data
        compose['services'] = services

        for compose_field in ['networks', 'volumes']:
            if compose_field in compose:
                compose[compose_field] = {f'{k}-{env}': v for k, v in compose[compose_field].items()}

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        compose_path = Path(f'{self.deploydir}/docker-compose-{env}.yml')
        with compose_path.open('w', encoding='utf-8') as fp:
            yaml.dump(compose, fp)
        self._add_permissions(compose_path)

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
    return parser.parse_args()


def main():
    args = parse_args()
    deploy = Deploy(deploydir=args.deploydir, silent=args.silent)
    deploy.start()


if __name__ == "__main__":
    main()
