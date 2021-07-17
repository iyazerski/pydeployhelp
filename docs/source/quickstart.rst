Quickstart
==========

Overview
--------

``pydeployhelp`` is aimed to help integrating deploy (*via Docker*) to
Python projects. It can be used both as external library (all processors
can be imported) and as CLI tool.

Following CLI tools will be available after installation:

-  ``pydeployhelp-quickstart``: creates directory with deploy service
   files templates (*Dockerfile, docker-compose, configs*)

-  ``pydeployhelp``: performs deploy according to info from deploy
   directory crated by ``pydeployhelp-quickstart``

Documentation
-------------

Please see the latest documentation at `Read the Docs <https://pydeployhelp.readthedocs.io/>`__

Installation
------------

``pydeployhelp`` can be installed from ``PyPi``:

.. code:: shell

    pip install pydeployhelp

Or locally (inside project directory):

.. code:: shell

    python setup.py install

``pydeployhelp-quickstart`` tool and all code library can be used
without any external system packages installation.

``pydeployhelp`` requires following external packages to be installed:

-  `Docker <https://docs.docker.com/>`__

-  `docker-compose <https://docs.docker.com/compose/>`__

Updating to newer versions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: shell

    python -m pip install --upgrade --no-cache-dir pydeployhelp

Usage
-----

pydeployhelp-quickstart
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: text

    usage: pydeployhelp-quickstart [-h] [-s] [-v]

    optional arguments:
      -h, --help    show this help message and exit
      -s, --silent  If specified, all communication with user will be ignored, default values will be used instead
      -v, --version         Print version and exit

Executing in ordinary way (without ``--silent``) you will be asked to
enter some info (*project name, deploy directory location, supported
tasks*), soon after that you will see message about service files
creation status.

pydeployhelp
~~~~~~~~~~~~

.. code:: text

    usage: pydeployhelp [-h] [-d DEPLOYDIR] [-s] [-v]

    optional arguments:
      -h, --help            show this help message and exit
      -d DEPLOYDIR, --deploydir DEPLOYDIR
                            Path to directory with deploy scripts (normally generated via `pydeployhelp-quickstart`)
      -s, --silent          If specified, all communication with user will be ignored, default values will be used instead
      -v, --version         Print version and exit

Executing in ordinary way (without ``--silent``) you will be asked to
enter some info (*task names, services names*), soon after that you will
see message about deploy status.
