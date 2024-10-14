# pydeployhelp

## Overview

`pydeployhelp` is a tool designed to simplify deploying Python projects using Docker. It can be used as a standalone CLI tool, offering flexibility in integrating deployment processes into your Python workflows.

After installation, the following CLI tools are available:

- `pydeployhelp`: Deploys your project based on the configuration found in the deployment directory created by `pydeployhelp-quickstart`.
- `pydeployhelp-quickstart`: Sets up a deployment directory with service file templates, including `Dockerfile`, `docker-compose`, and configuration files.

`pydeployhelp` makes it easy to containerize and manage your Python applications using Docker, saving you time and reducing complexity in the deployment phase.

## Documentation

For detailed instructions and the latest information, please visit the [official documentation at Read the Docs](https://pydeployhelp.readthedocs.io/).

## Installation

You can install `pydeployhelp` from [PyPI](https://pypi.org/project/pydeployhelp/):

```shell
pip install pydeployhelp
```

Or install it locally from the project directory:

```shell
pip install -e .
```

### Requirements

`pydeployhelp` requires [Docker](https://docs.docker.com/) to be installed on your system. The `pydeployhelp-quickstart` tool and the core library can be used without installing any additional system-level dependencies, making setup straightforward.

### Updating to the Latest Version

To update to the latest version of `pydeployhelp`, run the following command:

```shell
python -m pip install --upgrade --no-cache-dir pydeployhelp
```

## Usage

### `pydeployhelp`

The main command for deploying your project is `pydeployhelp`. Here is an overview of the available options:

```text
Usage: pydeployhelp [OPTIONS]

Main entrypoint, which will be called when executing `pydeployhelp` in console.

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --task                         TEXT  List of deployment tasks defined in config.yaml                                                                                             │
│ --target                       TEXT  List of deployment targets defined in config.yaml                                                                                           │
│ --deploydir                    TEXT  Path to directory with deploy scripts (normally generated via `pydeployhelp-quickstart`) [default: deploy]                                  │
│ --silent       --no-silent           Ignore all communication with user and use default values [default: no-silent]                                                              │
│ --version      --no-version          Print version and exit [default: no-version]                                                                                                │
│ --help                               Show this message and exit.                                                                                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Running `pydeployhelp` without the `--silent` flag will prompt you to provide information such as task names and services. Once completed, a status message regarding the deployment will be displayed.

Example of a non-interactive console mode (you won't be prompted for manual input):

```shell
pydeployhelp --task build --task up --target all
```

This command will run the specified deployment tasks (`build` and `up`) for all defined targets.

### `pydeployhelp-quickstart`

The `pydeployhelp-quickstart` command is used to generate a deployment directory with the necessary service templates. Here is how you can use it:

```text
Usage: pydeployhelp-quickstart [OPTIONS]

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --silent     --no-silent       Ignore all communication with user and use default values [default: no-silent]                                                                    │
│ --version    --no-version      Print version and exit [default: no-version]                                                                                                      │
│ --help                         Show this message and exit.                                                                                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Running `pydeployhelp-quickstart` without the `--silent` flag will prompt you to provide information such as the project name, deployment directory location, and supported tasks. Once completed, a status message will indicate the creation of the service files.

## Example Workflow

1. **Quickstart Setup**: Use `pydeployhelp-quickstart` to set up your deployment directory with service templates.
   ```shell
   pydeployhelp-quickstart
   ```
2. **Edit Configuration**: Customize the generated files (`Dockerfile`, `docker-compose`, etc.) in the deployment directory to suit your project.
3. **Deploy**: Run `pydeployhelp` to start deploying your project.
   ```shell
   pydeployhelp --task build --target all
   ```

This workflow helps you easily set up a Docker environment and manage your deployments effectively.

## Contributing

Contributions are welcome! If you have any ideas or find a bug, please open an issue or submit a pull request on [GitHub](https://github.com/iyazerski/pydeployhelp).

## License

`pydeployhelp` is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

If you have any questions or feedback, feel free to reach out to the project maintainer:
- GitHub: [iyazerski](https://github.com/iyazerski)

Thank you for using `pydeployhelp`! Happy deploying!
