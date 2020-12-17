from pathlib import Path
from typing import Dict, Union

BOOL_MAPPING = {'false': False, 'true': True}


def read_env_file(path: Union[str, Path], default_value='') -> Dict:
    """ Read environment variables from .env file """

    result = {}

    with path.open('r', encoding='utf-8') as fp:
        for line in fp:
            line = line.strip()
            if line.startswith('#') or '=' not in line:  # handle comments and invalid lines
                continue
            line_args = line.split('=')
            line_args_num = len(line_args)

            if line_args_num == 1:
                value = default_value
            elif line_args_num > 1:
                value = '='.join(line_args[1:]).strip().strip('\'"')
                value = BOOL_MAPPING.get(value.lower(), value)
            else:
                continue

            result[line_args[0].strip()] = value

    return result
