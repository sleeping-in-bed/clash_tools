Usage Guide
===========

clash_tools is a comprehensive toolkit that provides multiple command-line utilities for managing Clash proxy configurations and services. This guide covers all three main tools included in the package.

Installation
------------

Install using pip::

    pip install clash_tools

Or install from source::

    git clone <repository-url>
    cd clash_tools
    pip install -e .

Configuration
-------------

Clash Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~

All tools use a ``config.yaml`` file to configure the Clash proxy server. Default configuration::

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
        name: 'proxy_name'
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
          - 'proxy_name'

    rules:
      - MATCH,PROXY

Tools Overview
--------------

clash_serve - Service Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A comprehensive utility for Clash service management and configuration.

**Usage**::

    clash_serve [OPTIONS] COMMAND [ARGS]...

**Available Commands**:
  - ``run`` - Start the Clash service
  - ``config`` - Manage config.yaml file

**Description**:
  This tool provides two main functions: starting the Clash service and managing the configuration file. The ``run`` command starts the Clash service by running ``sudo ./clash -d ./`` in the script directory, while the ``config`` command helps manage the ``config.yaml`` file.

**Features**:
  - Service management with proper directory handling
  - Configuration file management
  - Built-in editor integration
  - Configuration file path display

clash_proxy - Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A shell script for setting up proxy environment variables in the current session.

**Usage**::

    eval "$(clash_proxy)"

**Description**:
  This script reads the configuration from ``config.yaml`` and sets up all necessary proxy environment variables for the current shell session.

**Environment Variables Set**:
  - ``http_proxy`` / ``HTTP_PROXY``
  - ``https_proxy`` / ``HTTPS_PROXY``
  - ``all_proxy`` / ``ALL_PROXY`` (SOCKS5)
  - ``no_proxy`` / ``NO_PROXY``

**Features**:
  - Automatic port detection from config file
  - Error handling and validation
  - Both lowercase and uppercase variable formats
  - Support for HTTP and SOCKS5 proxies

clash_docker - Docker Proxy Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A comprehensive Docker proxy management tool for enabling/disabling Docker proxy settings.

**Usage**::

    clash_docker [OPTIONS] COMMAND [ARGS]...

**Available Commands**:
  - ``enable`` - Enable Docker proxy settings
  - ``disable`` - Disable Docker proxy settings
  - ``status`` - Check current proxy status
  - ``reset`` - Reset all proxy configurations

Detailed Tool Usage
-------------------

clash_serve Commands
~~~~~~~~~~~~~~~~~~~~

run - Start Clash Service
^^^^^^^^^^^^^^^^^^^^^^^^^^

Start the Clash service with proper configuration::

    clash_serve run

**Description**:
  This command starts the Clash service by running ``sudo ./clash -d ./`` in the script directory. It automatically changes to the correct directory and ensures Clash runs with the proper configuration.

**Features**:
  - Automatically changes to the correct directory
  - Runs Clash with sudo privileges
  - Uses the current directory as the configuration directory

config - Manage Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Manage the config.yaml file::

    clash_serve config [OPTIONS]

**Options**::

    -e, --edit  Open config file in default editor
    --help      Show help information

**Examples**::

    # Display config file path
    clash_serve config

    # Edit config file with default editor
    clash_serve config --edit

    # Edit config file with specific editor
    EDITOR=vim clash_serve config --edit

**Description**:
  This command helps manage the ``config.yaml`` file. By default, it displays the absolute path of the configuration file. With the ``--edit`` option, it opens the file in your default editor.

**Features**:
  - Display configuration file absolute path
  - Open configuration file in editor
  - Respects ``EDITOR`` environment variable
  - Fallback to ``nano`` if no editor is set

clash_docker Commands
~~~~~~~~~~~~~~~~~~~~~

enable - Enable Docker Proxy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enable Docker proxy settings::

    clash_docker enable [OPTIONS]

**Options**::

    -p, --proxy TEXT  Specify proxy URL (default: http://127.0.0.1:7890)
    --help           Show help information

**Examples**::

    # Use default proxy settings
    clash_docker enable

    # Use custom proxy
    clash_docker enable --proxy http://192.168.1.100:8080

    # Use SOCKS5 proxy
    clash_docker enable -p socks5://127.0.0.1:1080

**This command will**:

1. Configure Docker client proxy (``~/.docker/config.json``)
2. If run with root privileges, also configure Docker daemon proxy (``/etc/systemd/system/docker.service.d/http-proxy.conf``)
3. Restart Docker service (only when configuring daemon proxy)

disable - Disable Docker Proxy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Disable Docker proxy settings::

    clash_docker disable

**This command will**:

1. Remove Docker client proxy configuration
2. If run with root privileges, also remove Docker daemon proxy configuration
3. Restart Docker service (only when removing daemon proxy)

status - Check Docker Proxy Status
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check current Docker proxy status::

    clash_docker status

**Example output**::

    === Docker Proxy Status ===
    🟢 Docker client proxy: Enabled
       HTTP Proxy: http://127.0.0.1:7890
       HTTPS Proxy: http://127.0.0.1:7890
       No Proxy: localhost,127.0.0.1,::1
    🟢 Docker daemon proxy: Enabled
       Configuration:
       Environment="HTTP_PROXY=http://127.0.0.1:7890"
       Environment="HTTPS_PROXY=http://127.0.0.1:7890"
       Environment="NO_PROXY=localhost,127.0.0.1,::1"

reset - Reset Docker Proxy Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reset all Docker proxy configurations::

    clash_docker reset

**This command will completely remove**:

- Docker client proxy configuration
- Docker daemon proxy configuration

Permission Requirements
-----------------------

clash_serve
~~~~~~~~~~~

Requires ``sudo`` privileges to run the Clash service.

clash_proxy
~~~~~~~~~~~

No special permissions required. Can be run by any user.

clash_docker
~~~~~~~~~~~~

**Client Proxy**: Docker client proxy configuration doesn't require special permissions and can be operated by regular users.

**Daemon Proxy**: Docker daemon proxy configuration requires root privileges because it needs to:

1. Modify systemd service configuration files
2. Restart Docker service

If you don't have root privileges, the tool will display a warning message but will still configure the client proxy.

Workflow Examples
-----------------

Complete Setup Workflow
~~~~~~~~~~~~~~~~~~~~~~~~

Here's a complete workflow for setting up Clash with all tools::

    # 1. Start Clash service
    clash_serve

    # 2. In a new terminal, set up environment variables
    source clash_proxy

    # 3. Test that proxy is working
    curl -I http://google.com

    # 4. Configure Docker proxy
    sudo clash_docker enable

    # 5. Verify Docker proxy status
    clash_docker status

    # 6. Test Docker with proxy
    docker pull hello-world

Development Workflow
~~~~~~~~~~~~~~~~~~~~

For development environments::

    # Terminal 1: Start Clash service
    clash_serve

    # Terminal 2: Set up development environment
    source clash_proxy

    # Now all commands in this terminal will use the proxy
    npm install
    pip install -r requirements.txt
    git clone https://github.com/example/repo.git

Docker-Only Workflow
~~~~~~~~~~~~~~~~~~~~

If you only need Docker proxy support::

    # Ensure Clash is running (in background or another terminal)
    clash_serve &

    # Enable Docker proxy
    sudo clash_docker enable

    # Use Docker normally
    docker pull nginx
    docker run -d nginx

    # When done, disable proxy
    sudo clash_docker disable

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Issue 1: clash_serve Permission Denied**

If you get permission errors when running ``clash_serve``, ensure:

1. The ``clash`` binary is executable: ``chmod +x clash``
2. You have sudo privileges
3. The config file exists in the same directory

**Issue 2: clash_proxy Variables Not Set**

If environment variables aren't being set:

1. Make sure to use ``source clash_proxy`` (not just ``./clash_proxy``)
2. Check that ``config.yaml`` exists and contains valid port numbers
3. Verify the script has read permissions

**Issue 3: Docker Proxy Issues**

For Docker proxy problems, see the detailed troubleshooting in the clash_docker section above.

**Issue 4: Config File Not Found**

If any tool reports config file not found:

1. Ensure ``config.yaml`` exists in the same directory as the scripts
2. Check file permissions (should be readable)
3. Verify the YAML syntax is correct

Debug Information
~~~~~~~~~~~~~~~~~

Check Clash service status::

    ps aux | grep clash

Check if ports are listening::

    netstat -tuln | grep 7890
    netstat -tuln | grep 7891

View environment variables::

    env | grep -i proxy

Best Practices
--------------

1. **Start Clash First**: Always start the Clash service before using other tools
2. **Use Absolute Paths**: When running scripts from different directories, use absolute paths
3. **Check Service Status**: Verify Clash is running before configuring proxies
4. **Terminal Sessions**: Remember that ``clash_proxy`` only affects the current terminal session
5. **Backup Configs**: Keep backups of your ``config.yaml`` file
6. **Test Connectivity**: Always test proxy connectivity after configuration

Advanced Usage
--------------

Custom Configuration Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can modify ``clash_serve`` to use a custom configuration directory by editing the script.

Automated Scripts
~~~~~~~~~~~~~~~~~

Create shell scripts to automate common workflows::

    #!/bin/bash
    # start-clash-env.sh

    # Start Clash in background
    clash_serve &
    CLASH_PID=$!

    # Wait for service to start
    sleep 2

    # Set environment variables
    source clash_proxy

    # Configure Docker
    sudo clash_docker enable

    echo "Clash environment ready!"
    echo "Use 'kill $CLASH_PID' to stop Clash service"

Environment-Specific Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can maintain different config files for different environments::

    # Development
    cp config.dev.yaml config.yaml
    clash_serve

    # Production
    cp config.prod.yaml config.yaml
    clash_serve

Integration with Other Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tools can be integrated with other development tools::

    # In your .bashrc or .zshrc
    alias start-proxy="clash_serve & sleep 2 && source clash_proxy"
    alias stop-proxy="pkill clash && unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY"
