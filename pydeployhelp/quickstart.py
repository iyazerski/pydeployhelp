#!/usr/bin/env python
import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Set

from ruamel.yaml import YAML

from pydeployhelp import __version__
from pydeployhelp.base import ABC, Configs


@dataclass
class QuickstartDefaults:
    deploy_dir: str
    deploy_tasks: Set[str]
    dockerfile: str


class Quickstart(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def start(self):
        """ Receive info from user input and create deploy directory scripts """

        try:
            project_name = self.enter_project_name()
            deploy_dir = self.enter_deploy_dir()
            deploy_tasks = self.enter_deploy_tasks()
            self.ask_to_continue()
        except (KeyboardInterrupt, InterruptedError):
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
                raise InterruptedError  # prevent from RecursionError

            return self.enter_deploy_dir()

        deploy_dir.mkdir(exist_ok=True, parents=True)
        self._add_permissions(deploy_dir)

        return deploy_dir

    def enter_deploy_tasks(self) -> Set[str]:
        """ Receive deploy tasks names from user input """

        allowed_tasks = list(self.defaults.deploy_tasks)
        return self.enter(allowed_items=allowed_tasks, default='all', items_name='deploy tasks')

    def create_config_file(self, deploy_dir: Path, deploy_tasks: Set[str]):
        """ Create file with deploy configs and tasks pipeline """

        configs = Configs(
            context=dict(env_file='.env', compose=f'{deploy_dir}/docker-compose-template.j2'),
            tasks={task: [dict(
                title=f'{task} all',
                pipeline=[f'docker-compose -f {deploy_dir}/docker-compose-{"{ENV}"}.yml {task}']
            )] for task in deploy_tasks}
        )

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        configs_path = Path(f'{deploy_dir}/config.yml')
        with configs_path.open('w', encoding='utf-8') as fp:
            yaml.dump(configs.dict(), fp)

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
                project_name + '-{{ ENV }}': {
                    'build': {
                        'context': '..',
                        'dockerfile': f'{deploy_dir}/Dockerfile'
                    },
                    'image': project_name + ':{{ ENV }}',
                    'container_name': project_name + '-{{ ENV }}'
                }
            }
        }
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        compose_path = Path(f'{deploy_dir}/docker-compose-template.j2')
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
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Print version and exit'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.version:
        print(f'pydeployhelp-quickstart version {__version__}')
    else:
        quickstart = Quickstart(silent=args.silent)
        quickstart.start()


if __name__ == "__main__":
    main()
