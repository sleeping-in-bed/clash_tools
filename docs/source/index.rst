clash_tools documentation
=========================

**GitHub Repository**: `sleeping-in-bed/clash_tools <https://github.com/sleeping-in-bed/clash_tools>`_

.. image:: https://img.shields.io/pypi/v/clash-tools.svg
   :target: https://pypi.org/project/clash-tools/
   :alt: PyPI version
.. image:: https://static.pepy.tech/badge/clash-tools
   :target: https://pepy.tech/projects/clash-tools
   :alt: PyPI downloads
.. image:: https://github.com/sleeping-in-bed/clash_tools/actions/workflows/test.yml/badge.svg?branch=main
   :target: https://github.com/sleeping-in-bed/clash_tools/actions/workflows/test.yml
   :alt: Test status
.. image:: https://codecov.io/github/sleeping-in-bed/clash_tools/graph/badge.svg?token=HEIMHMX0PK
   :target: https://codecov.io/github/sleeping-in-bed/clash_tools
   :alt: Codecov

clash_tools is a comprehensive collection of utilities for managing Clash proxy configurations and services. It provides multiple command-line tools for different purposes, making it easy to work with Clash in various environments.

Tools Overview
--------------

The toolkit includes four main utilities:

**wireguard**
  A tool to manage WireGuard server and client configurations.

  Key highlights:
  - User config directory: ``$XDG_CONFIG_HOME/clash_tools/wireguard/`` or ``~/.config/clash_tools/wireguard/``
  - Config commands support ``--path``/``--edit``/``--cat``
  - Service lifecycle: ``up``/``down``/``restart`` and client ``check-ip``

**clash_docker**
  Docker proxy management tool for enabling/disabling Docker proxy settings

**clash_proxy**
  Shell script for setting up proxy environment variables in the current session

**clash_serve**
  Service management tool for starting the Clash service and managing configuration files

Features
--------

- 🚀 **Docker Integration**: One-click enable/disable Docker client and daemon proxy
- 🔧 **Environment Setup**: Easy proxy environment variable configuration
- 🎯 **Service Management**: Simple Clash service startup and management
- 📊 **Status Monitoring**: Real-time proxy status checking
- 🔄 **Configuration Reset**: Convenient reset functionality
- 💻 **Multi-platform**: Works on Linux systems with systemd support

Quick Start
-----------

Installation::

    pip install clash_tools

Basic Usage::

    # Start Clash service
    clash_serve

    # Set proxy environment variables
    source clash_proxy

    # Configure Docker proxy
    clash_docker enable

    # Check Docker proxy status
    clash_docker status

    # Disable Docker proxy
    clash_docker disable

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   clash_tools/index
   wireguard/index

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
