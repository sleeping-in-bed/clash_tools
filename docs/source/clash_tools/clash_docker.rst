`clash_docker` - Docker Proxy Management
========================================


A comprehensive Docker proxy management tool for enabling/disabling Docker proxy settings.

**Usage**::

    clash_docker [OPTIONS] COMMAND [ARGS]...

**Available Commands**:
  - ``enable`` - Enable Docker proxy settings
  - ``disable`` - Disable Docker proxy settings
  - ``status`` - Check current proxy status
  - ``reset`` - Reset all proxy configurations

Detailed Commands
-----------------

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

**Client Proxy**: Docker client proxy configuration doesn't require special permissions and can be operated by regular users.

**Daemon Proxy**: Docker daemon proxy configuration requires root privileges because it needs to:

1. Modify systemd service configuration files
2. Restart Docker service

If you don't have root privileges, the tool will display a warning message but will still configure the client proxy.

Troubleshooting
---------------

**Issue: Docker Proxy Issues**

For Docker proxy problems, see the detailed troubleshooting in the clash_docker section above.
