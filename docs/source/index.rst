clash_tools documentation
=========================

clash_tools is a comprehensive collection of utilities for managing Clash proxy configurations and services. It provides multiple command-line tools for different purposes, making it easy to work with Clash in various environments.

Tools Overview
--------------

The toolkit includes three main utilities:

**clash_docker**
  Docker proxy management tool for enabling/disabling Docker proxy settings

**clash_proxy**
  Shell script for setting up proxy environment variables in the current session

**clash_serve**
  Simple utility for starting the Clash service with proper configuration

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

   usage

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
