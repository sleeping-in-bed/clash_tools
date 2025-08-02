WireGuard Management (`wireguard`)
==================================

The ``wireguard`` utility is a powerful command-line tool for deploying and managing WireGuard servers and clients using Docker and Docker Compose. It simplifies the entire process, from generating configurations to controlling the services.

This tool is designed to be self-contained within the ``clash_tools/wireguard`` directory.

Core Features
-------------

- **Automated Configuration**: Generates all necessary WireGuard and Docker Compose configuration files from simple Python settings.
- **Service Management**: Easily start, stop, and manage server and client services with ``up`` and ``down`` commands.
- **Key Generation**: Includes a helper command to generate WireGuard key pairs.
- **Easy Editing**: Open configuration files directly in your default editor.

Workflow
--------

1.  **Install WireGuard (if needed)**: If the ``wg`` command-line tool is not installed, run ``wireguard install-wg`` to install it on Debian-based systems (like Ubuntu).
2.  **Generate Keys**: Use ``wireguard genkey`` to create private/public key pairs for the server and each client.
3.  **Configure**: Fill in the ``server_settings.py`` and ``client_settings.py`` files with the generated keys and your desired network settings.
4.  **Deploy**: Run ``wireguard server up`` on your server machine and ``wireguard client up`` on your client machine.

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2

   server
   client

Utility Commands
----------------

install-wg
~~~~~~~~~~

Installs the `wireguard` command-line tools on Debian-based systems (like Ubuntu) using `apt`. This command requires `sudo` privileges.

**Usage**::

    wireguard install-wg

genkey
~~~~~~

Generate a new WireGuard private and public key pair. These keys are essential for configuring both the server and clients.

**Usage**::

    wireguard genkey

**Example Output**::

    🔑 New key pair generated successfully!

    PrivateKey: <Your-New-Private-Key>
    PublicKey:  <Your-New-Public-Key>


config
~~~~~~

View the path to or edit the configuration files for the server or client.

**Usage**::

    # View path to server settings
    wireguard config server

    # Edit server settings in your default editor
    wireguard config server --edit

    # View path to client settings
    wireguard config client

    # Edit client settings
    wireguard config client --edit
