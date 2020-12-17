# pydeployhelp

## Overview

`pydeployhelp` is aimed to help integrating deploy (*via Docker*) to Python projects. It can be used both as
external library (all processors can be imported) and as CLI tool.

Following CLI tools will be available after installation:

- `pydeployhelp-quickstart`: creates directory with deploy service files templates (*Dockerfile, docker-compose, configs*)

- `pydeployhelp-deploy`: performs deploy according to info from deploy directory crated by `pydeployhelp-quickstart`

## Installation

`pydeployhelp` can be installed from `PyPi`:

```properties
pip install pydeployhelp
```

Or locally (inside project directory):

```properties
python setup.py install
```

`pydeployhelp-quickstart` tool and all code library can be used without any external system packages installation.

`pydeployhelp-deploy` requires following external packages to be installed:

- [Docker](https://docs.docker.com/)

- [docker-compose](https://docs.docker.com/compose/)

## Usage

### pydeployhelp-quickstart

Open terminal and execute following:

```properties
pydeployhelp-quickstart
```

Then you will be asked to enter some info (*project name, deploy directory location, supported tasks*),
soon after that you will see message about service files creation status.
