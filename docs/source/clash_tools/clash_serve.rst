`clash_serve` - Service Management
==================================

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

Detailed Commands
-----------------

run - Start Clash Service
^^^^^^^^^^^^^^^^^^^^^^^^^

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

Permission Requirements
-----------------------

Requires ``sudo`` privileges to run the Clash service.

Troubleshooting
---------------

**Issue: clash_serve Permission Denied**

If you get permission errors when running ``clash_serve``, ensure:

1. The ``clash`` binary is executable: ``chmod +x clash``
2. You have sudo privileges
3. The config file exists in the same directory
