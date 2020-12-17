#!/usr/bin/env python
import argparse
import os
from pathlib import Path
from typing import NamedTuple, Set

from ruamel.yaml import YAML


class QuickstartDefaults(NamedTuple):
    deploy_dir: str
    deploy_tasks: Set[str]
    dockerfile: str


class Quickstart:
    def __init__(self, silent: bool = False):
        self.silent = silent
        self.defaults = QuickstartDefaults(
            deploy_dir='deploy',
            deploy_tasks={'build', 'up', 'down'},
            dockerfile="""# use some base image
            FROM python:buster

            # run console commands inside image
            RUN python -m pip install --upgrade pip wheel setuptools
            RUN mkdir {project_name}

            # change current directory inside image
            WORKDIR {project_name}

            # copy files from host to image
            COPY requirements.txt .
            """
        )

    def _print_service_message(self, message: str, warning: bool = False, error: bool = False):
        if not self.silent or error:
            print(f'\x1b[1;3{1 if error else 3 if warning else 2};40m{message}\x1b[0m')

    def _add_permissions(self, path: Path):
        try:
            path.chmod(0o777)  # TODO: use permissions from params
        except PermissionError:
            self._print_service_message(f'Unable to change permissions for "{path}"', warning=True)

    def start(self):
        """ Receive info from user input and create deploy directory scripts """

        try:
            project_name = self.enter_project_name()
            deploy_dir = self.enter_deploy_dir()
            deploy_tasks = self.enter_deploy_tasks()
        except KeyboardInterrupt:
            self._print_service_message('Interrupted', error=True)
        else:
            self._print_service_message(f'Creating service files for project "{project_name}" at "{deploy_dir}":')
            self.create_config_file(deploy_dir, deploy_tasks)
            self.create_dockerfile(deploy_dir, project_name)
            self.create_compose(deploy_dir, project_name)
            self._print_service_message('Done!')

    def enter_project_name(self) -> str:
        """ Receive project name from user input """

        project_name = Path(os.getcwd()).name
        if not self.silent:
            project_name = input(f'Enter project name [{project_name}]: ').strip() or project_name
        return project_name

    def enter_deploy_dir(self) -> Path:
        """ Receive deploy directory path from user input """

        deploy_dir = self.defaults.deploy_dir
        if not self.silent:
            deploy_dir = input(
                f'Enter directory path where deploy scripts should be created [{deploy_dir}]: '
            ).strip() or deploy_dir

        deploy_dir = Path(deploy_dir)
        if deploy_dir.exists() and not deploy_dir.is_dir():
            self._print_service_message(f'"{deploy_dir}"" is not a valid directory path, please try again', error=True)

            if self.silent:
                raise KeyboardInterrupt  # prevent from RecursionError

            return self.enter_deploy_dir()

        deploy_dir.mkdir(exist_ok=True, parents=True)
        self._add_permissions(deploy_dir)

        return deploy_dir

    def enter_deploy_tasks(self) -> Set[str]:
        """ Receive deploy tasks names from user input """

        deploy_tasks = self.defaults.deploy_tasks
        defaults = ','.join(deploy_tasks)
        if not self.silent:
            deploy_tasks = set(filter(
                lambda x: x in self.defaults.deploy_tasks,
                (task.strip().lower() for task in input(
                    f'Enter comma separated deploy tasks names from following: {defaults} [{defaults}]: '
                ).strip().split(','))
            )) or deploy_tasks
        return deploy_tasks

    def create_config_file(self, deploy_dir: Path, deploy_tasks: Set[str]):
        """ Create file with deploy configs and tasks pipeline """

        data = {
            'context': {
                'env_file': '.env'
            },
            'tasks': {
                task: [
                    {
                        'title': f'{task} all',
                        'pipeline': [f'docker-compose -f {deploy_dir}/docker-compose-{"{ENV}"}.yml {task}']
                    }
                ] for task in deploy_tasks
            }
        }

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        configs_path = Path(f'{deploy_dir}/config.yml')
        with configs_path.open('w', encoding='utf-8') as fp:
            yaml.dump(data, fp)

        self._add_permissions(configs_path)
        self._print_service_message('\tconfigs\t\t\N{check mark}')

    def create_dockerfile(self, deploy_dir: Path, project_name: str):
        """ Create file with instructions for Docker daemon to build an image """

        dockerfile_path = Path(f'{deploy_dir}/Dockerfile')
        with dockerfile_path.open('w', encoding='utf-8') as fp:
            for line in self.defaults.dockerfile.format(project_name=project_name).splitlines():
                fp.write(f'{line.strip()}\n')

        self._add_permissions(dockerfile_path)
        self._print_service_message('\tdockerfile\t\N{check mark}')

    def create_compose(self, deploy_dir: Path, project_name: str):
        data = {
            'version': '3',
            'services': {
                project_name: {
                    'build': {
                        'context': '..',
                        'dockerfile': f'{deploy_dir}/Dockerfile'
                    },
                    'image': project_name,
                    'container_name': project_name
                }
            }
        }
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        compose_path = Path(f'{deploy_dir}/docker-compose.yml')
        with compose_path.open('w', encoding='utf-8') as fp:
            yaml.dump(data, fp)

        self._add_permissions(compose_path)
        self._print_service_message('\tdocker-compose\t\N{check mark}')


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--silent',
        action='store_true',
        help='If specified, all communication with user will be ignored, default values will be used instead'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    quickstart = Quickstart(silent=args.silent)
    quickstart.start()


if __name__ == "__main__":
    main()
