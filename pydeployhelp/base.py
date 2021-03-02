import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


class ABC(abc.ABC):
    def __init__(self, silent: bool = False):
        self.silent = silent
        self.colors = {
            color: i
            for i, color in enumerate(['black', 'red', 'green', 'orange', 'blue', 'purple', 'yellow', 'white'])
        }
        self.mark = self._colorize_string('\N{check mark}', color='green')

    def _colorize_string(self, text: str, color: str = 'white') -> str:
        """ Colorize `text`

        Parameters
        ----------

        text : str
            Text to be colorized
        color : str, default=white
            Text color. Choices: black, red, green, orange, blue, purple, yellow, white
        """

        color_code = self.colors.get(color, 7)
        return f'\x1b[1;3{color_code};40m{text}\x1b[0m'

    def _print_service_message(self, message: str, warning: bool = False, error: bool = False):
        """ Print colorized messages """

        if not self.silent or error:
            print(self._colorize_string(message, color='red' if error else 'orange' if warning else 'green'))

    def _add_permissions(self, path: Path):
        try:
            path.chmod(0o777)  # TODO: use permissions from params
        except PermissionError:
            self._print_service_message(f'Unable to change permissions for "{path}"', warning=True)

    def _remove_file(self, path: Path):
        try:
            path.unlink()
        except PermissionError:
            self._print_service_message(f'Unable to delete file "{path}"', warning=True)

    def ask_to_continue(self) -> bool:
        """ Receive agreement from user to continue """

        agreement = input('Do you agree to start processing (yes or no)? [yes]: ').strip().lower() or 'yes'
        if agreement == 'yes':
            agree = True
        elif agreement == 'no':
            agree = False
        else:
            agree = self.ask_to_continue()
        if not agree:
            raise InterruptedError

    def enter(self, allowed_items: List[str], default: str, items_name: str) -> List[str]:
        if self.silent:
            if default == 'all':
                items = allowed_items
            else:
                items = [default]
        else:
            choices = []

            if default == 'all':
                choices.append(self._colorize_string('all', color='green'))
                choices.append('|')
                choices.append(self._colorize_string(' '.join(allowed_items), color='blue'))
            else:
                choices.append(self._colorize_string('all', color='blue'))
                choices.append('|')
                choices.append(self._colorize_string(default, color='green'))
                if len(allowed_items) != 1:
                    choices.append(self._colorize_string(' '.join(allowed_items[1:]), color='blue'))

            choices = ' '.join(choices)
            user_input = input(f'Enter {items_name} from following: {choices}: ').replace(',', ' ').strip() or default
            items = list(filter(
                lambda x: x in allowed_items or x == 'all',
                [item.strip().lower() for item in user_input.split()]
            ))

            if not items:
                return self.enter(allowed_items, default, items_name)

            if 'all' in items:
                items = allowed_items

            print(
                f'\t{self.mark} processing {items_name}: {self._colorize_string(" ".join(items), color="green")}'
            )

        return items

    @abc.abstractmethod
    def start(self):
        ...


@dataclass
class Configs:
    context: Dict = field(default_factory=dict)
    tasks: Dict = field(default_factory=dict)
