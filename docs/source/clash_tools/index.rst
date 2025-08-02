Clash Tools Guide
=================

clash_tools is a comprehensive toolkit that provides multiple command-line utilities for managing Clash proxy configurations and services. This guide covers all the main tools included in the package.

.. toctree::
   :maxdepth: 2
   :caption: Tools:

   clash_serve
   clash_proxy
   clash_docker

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

Workflow Examples
-----------------

Complete Setup Workflow
~~~~~~~~~~~~~~~~~~~~~~~~

Here's a complete workflow for setting up Clash with all tools::

    # 1. Start Clash service
    clash_serve

    # 2. In a new terminal, set up environment variables
    eval "$(clash_proxy)"

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
    eval "$(clash_proxy)"

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
    eval "$(clash_proxy)"

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
    alias start-proxy="clash_serve & sleep 2 && eval \"$(clash_proxy)\""
    alias stop-proxy="pkill clash && unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY"

Troubleshooting
---------------

General Issues
~~~~~~~~~~~~~~

**Issue: Config File Not Found**

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
