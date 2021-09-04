import abc
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List

import typer


class ABC(abc.ABC):
    """ Parent class for all CLI tools, contains common methods related to user i/o """

    def __init__(self, silent: bool = False):
        self.silent = silent

    def _print_service_message(self, message: str, force: bool = False, color: str = typer.colors.WHITE, **kwargs):
        """ Print colorized messages """

        if not self.silent or force:
            typer.echo(typer.style(message, fg=color, **kwargs))

    def _add_permissions(self, path: Path):
        """ Add full permissions (rwx) for all users (ugo) to specified file.
        This can be necessary for correct file deletion """

        try:
            path.chmod(0o777)  # TODO: use permissions from params
        except PermissionError:
            self._print_service_message(f'Unable to change permissions for "{path}"', color=typer.colors.YELLOW)

    def _remove_file(self, path: Path):
        """ Remove specified file from filesystem """

        try:
            path.unlink()
        except PermissionError:
            self._print_service_message(f'Unable to delete file "{path}"', color=typer.colors.YELLOW)

    def ask_to_continue(self) -> None:
        """ Receive agreement from user input to continue """

        agree = typer.confirm('Do you agree to start processing?')
        if not agree:
            raise typer.Abort()

    def enter(self, allowed_items: List[str], default: str, items_name: str) -> List[str]:
        """ Receive answer from user input for provided list of available choices """

        if self.silent:
            if default == 'all':
                items = allowed_items
            else:
                items = [default]
        else:
            choices = []

            if default == 'all':
                choices.append(typer.style('all', fg=typer.colors.GREEN))
                choices.append('|')
                choices.append(typer.style(' '.join(allowed_items), fg=typer.colors.BLUE))
            else:
                choices.append(typer.style('all', fg=typer.colors.BLUE))
                choices.append('|')
                choices.append(typer.style(default, fg=typer.colors.GREEN))
                if len(allowed_items) != 1:
                    choices.append(typer.style(' '.join(allowed_items[1:]), fg=typer.colors.BLUE))

            choices = ' '.join(choices)
            user_input = typer.prompt(f'Enter {items_name} from following: {choices}', default=default)
            items = list(filter(
                lambda x: x in allowed_items or x == 'all',
                [item.strip().lower() for item in user_input.split()]
            ))

            if not items:
                return self.enter(allowed_items, default, items_name)

            if 'all' in items:
                items = allowed_items

            typer.echo(
                f'\t{items_name}: {typer.style(", ".join(items), fg=typer.colors.GREEN)}'
            )

        return items

    @abc.abstractmethod
    def start(self):
        ...


@dataclass
class Configs:
    context: Dict = field(default_factory=dict)
    tasks: Dict = field(default_factory=dict)

    def dict(self) -> Dict:
        return asdict(self)
