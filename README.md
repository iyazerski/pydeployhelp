# pydeployhelp

## Overview

`pydeployhelp` is aimed to help integrating deploy (*via Docker*) to Python projects. It can be used both as
external library (all processors can be imported) and as CLI tool.

Following CLI tools will be available after installation:

- `pydeployhelp`: performs deploy according to info from deploy directory created by `pydeployhelp-quickstart`
- `pydeployhelp-quickstart`: creates directory with deploy service files templates (*Dockerfile, docker-compose, configs*)

## Documentation

Please see the latest documentation at [Read the Docs](https://pydeployhelp.readthedocs.io/)

## Installation

`pydeployhelp` can be installed from `PyPi`:

```shell
pip install pydeployhelp
```

Or locally (inside project directory):

```shell
pip install -e .
```

`pydeployhelp` requires following external packages to be installed:

- [Docker](https://docs.docker.com/)

`pydeployhelp-quickstart` tool and all code library can be used without any external system packages installation.

### Updating to newer versions

```shell
python -m pip install --upgrade --no-cache-dir pydeployhelp
```

## Usage

### pydeployhelp

```text
Usage: pydeployhelp [OPTIONS]                                                                                                                                                      

Main entrypoint, which will be called when executing `pydeployhelp` in console                                                                                                     

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --task                         TEXT  List of deployment tasks defined in config.yaml                                                                                             │
│ --target                       TEXT  List of deployment targets defined in config.yaml                                                                                           │
│ --deploydir                    TEXT  Path to directory with deploy scripts (normally generated via `pydeployhelp-quickstart`) [default: deploy]                                  │
│ --silent       --no-silent           Ignore all communication with user and use default values [default: no-silent]                                                              │
│ --version      --no-version          Print version and exit [default: no-version]                                                                                                │
│ --help                               Show this message and exit.                                                                                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Executing in ordinary way (without `--silent`) you will be asked to enter some info
(*task names, services names*),
soon after that you will see message about deploy status.

Console mode example (you will not be asked to enter any info manually):

```shell
pydeployhelp --task build --task up --target all
```

### pydeployhelp-quickstart

```text
Usage: pydeployhelp-quickstart [OPTIONS]                                                                                                                                           

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --silent     --no-silent       Ignore all communication with user and use default values [default: no-silent]                                                                    │
│ --version    --no-version      Print version and exit [default: no-version]                                                                                                      │
│ --help                         Show this message and exit.                                                                                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Executing in ordinary way (without `--silent`) you will be asked to enter some info
(*project name, deploy directory location, supported tasks*),
soon after that you will see message about service files creation status.
