clash_tools - Clash Proxy Management Toolkit
============================================

clash_tools is a comprehensive collection of utilities for managing Clash proxy configurations and services. It provides multiple command-line tools for different purposes, making it easy to work with Clash in various environments.

Docs: https://clash-tools.readthedocs.io/en/latest/

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

Features
--------

- 🚀 **Docker Integration**: One-click enable/disable Docker client and daemon proxy
- 🔧 **Environment Setup**: Easy proxy environment variable configuration
- 🎯 **Service Management**: Simple Clash service startup and management
- 📊 **Status Monitoring**: Real-time proxy status checking
- 🔄 **Configuration Reset**: Convenient reset functionality
- 💻 **Multi-platform**: Works on Linux systems with systemd support

Tools Overview
--------------

The toolkit includes three main utilities:

**clash_docker**
  Docker proxy management tool for enabling/disabling Docker proxy settings

**clash_proxy**
  Shell script for setting up proxy environment variables in the current session

**clash_serve**
  Simple utility for starting the Clash service with proper configuration

Installation
------------

To install **clash_tools**, use pip:

.. code-block:: console

   $ python -m pip install clash_tools

Quick Start
-----------

1. **Start Clash service**:

.. code-block:: console

   $ clash_serve

2. **Set up proxy environment variables** (in a new terminal):

.. code-block:: console

   $ source clash_proxy

3. **Configure Docker proxy**:

.. code-block:: console

   $ clash_docker enable

4. **Check proxy status**:

.. code-block:: console

   $ clash_docker status

5. **Disable proxy when done**:

.. code-block:: console

   $ clash_docker disable

Configuration
-------------

All tools use a ``config.yaml`` file to configure the Clash proxy server.

Example configuration:

.. code-block:: yaml

   port: 7890
   socks-port: 7891
   redir-port: 7892
   allow-lan: true
   mode: rule
   log-level: info
   external-controller: '0.0.0.0:9090'
   secret: ''

   proxies:
     -
       name: 'my-proxy'
       type: ss
       server: your-proxy-server
       port: your-proxy-port
       cipher: your-cipher
       password: your-password
       udp: true

   proxy-groups:
     - name: "PROXY"
       type: select
       proxies:
         - 'my-proxy'

   rules:
     - MATCH,PROXY

Usage Examples
--------------

**Complete Workflow**:

.. code-block:: console

   # Terminal 1: Start Clash service
   $ clash_serve

   # Terminal 2: Set up environment and test
   $ source clash_proxy
   $ curl -I http://google.com
   $ sudo clash_docker enable
   $ docker pull hello-world

**Development Environment**:

.. code-block:: console

   $ source clash_proxy
   $ npm install
   $ pip install -r requirements.txt
   $ git clone https://github.com/example/repo.git

**Docker-Only Setup**:

.. code-block:: console

   $ clash_serve &
   $ sudo clash_docker enable
   $ docker pull nginx

Documentation
-------------

For detailed documentation, visit: https://clash-tools.readthedocs.io/

The documentation includes:

- Complete installation guide
- Detailed usage instructions for all tools
- Configuration examples
- Troubleshooting guide
- Best practices and workflows

Contributing
------------

Contributions are welcome! Please feel free to submit a Pull Request.

License
-------

This project is licensed under the MIT License.
