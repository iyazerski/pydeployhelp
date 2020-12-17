import abc
from pathlib import Path
from typing import Dict

from pydantic import BaseModel


class ABC(abc.ABC):
    def __init__(self, silent: bool = False):
        self.silent = silent

    @staticmethod
    def _format_defaults(text: str) -> str:
        return f'\x1b[1;34;40m{text}\x1b[0m'

    def _print_service_message(self, message: str, warning: bool = False, error: bool = False):
        """ Print colorized messages """

        if not self.silent or error:
            print(f'\x1b[1;3{1 if error else 3 if warning else 2};40m{message}\x1b[0m')

    def _add_permissions(self, path: Path):
        try:
            path.chmod(0o777)  # TODO: use permissions from params
        except PermissionError:
            self._print_service_message(f'Unable to change permissions for "{path}"', warning=True)

    @abc.abstractmethod
    def start(self):
        ...


class Configs(BaseModel):
    context: Dict = {}
    tasks: Dict = {}
