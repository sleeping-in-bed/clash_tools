`clash_serve` - Service Management
==================================

A comprehensive utility for Clash service management and configuration.

**Usage**::

    clash_serve [OPTIONS] COMMAND [ARGS]...

**Available Commands**:
  - ``run`` - Start the Clash service manually
  - ``config`` - Manage config.yaml file
  - ``service`` - Manage Clash as a systemd service

**Description**:
  This tool provides functions for running Clash manually, managing its configuration, and controlling it as a systemd service.

**Features**:
  - Manual service execution
  - Systemd service management (add, remove, status)
  - Configuration file management with editor integration

Detailed Commands
-----------------

run - Start Clash Service Manually
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start the Clash service with proper configuration::

    clash_serve run

**Description**:
  This command starts the Clash service by running ``sudo ./clash -d ./`` in the script directory. It is intended for manual, one-off execution. For a persistent background service, use the ``service`` command.

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

**Description**:
  This command helps manage the ``config.yaml`` file. By default, it displays the absolute path of the configuration file. With the ``--edit`` option, it opens the file in your default editor.

**Features**:
  - Display configuration file absolute path
  - Open configuration file in editor
  - Respects ``EDITOR`` environment variable

service - Manage as a Systemd Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Manage the clash systemd service for running it in the background persistently. All service commands require ``sudo`` privileges.

**Usage**::

    sudo clash_serve service [COMMAND]

**Available Commands**:
  - ``add`` - Install, enable, and start the service
  - ``remove`` - Stop, disable, and remove the service
  - ``status`` - Check the service status

**service add**
  Installs and starts the Clash service.

  ::

      sudo clash_serve service add

  This command will:
  1. Create a systemd service file at ``/etc/systemd/system/clash.service``.
  2. Configure the service to run as the current user.
  3. Reload the systemd daemon.
  4. Enable the service to start on boot.
  5. Start the service immediately.

**service remove**
  Stops and completely removes the Clash service.

  ::

      sudo clash_serve service remove

  This command will:
  1. Stop the running Clash service.
  2. Disable the service from starting on boot.
  3. Remove the systemd service file.
  4. Reload the systemd daemon.

**service status**
  Checks the current status of the Clash service.

  ::

      sudo clash_serve service status

  This will display detailed information from ``systemctl``, including whether the service is active, its PID, and recent log entries.

Permission Requirements
-----------------------

- ``run`` command requires ``sudo`` to start Clash.
- ``service`` subcommands (``add``, ``remove``) require ``sudo`` to interact with systemd. The ``status`` command may also require it depending on system configuration.
- ``config`` command does not require special permissions unless the file itself requires it.

Troubleshooting
---------------

**Issue: Permission Denied**

If you get permission errors when running ``clash_serve``, ensure:

1. You are using ``sudo`` for ``run`` and ``service`` commands.
2. The ``clash`` binary is executable: ``chmod +x clash``
3. The config file exists in the same directory.
