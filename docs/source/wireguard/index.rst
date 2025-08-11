WireGuard Management (`wireguard`)
==================================

The ``wireguard`` utility is a powerful command-line tool for deploying and managing WireGuard servers and clients using Docker and Docker Compose. It simplifies the entire process, from generating configurations to controlling the services.

Configuration files are stored in the user's config directory following the XDG Base Directory specification:

- If ``XDG_CONFIG_HOME`` is set: ``$XDG_CONFIG_HOME/clash_tools/wireguard/``
- Otherwise: ``~/.config/clash_tools/wireguard/``

Core Features
-------------

- **Automated Configuration**: Generates all necessary WireGuard and Docker Compose configuration files from simple Python settings.
- **Service Management**: Easily start, stop, and manage server and client services with ``up`` and ``down`` commands.
- **Restart Support**: Quickly restart server or client with a single command (``restart``).
- **Key Generation**: Includes a helper command to generate WireGuard key pairs.
- **Config Management**: View path, open in your editor, or print contents of config files with flexible options.

Workflow
--------

1.  **Install WireGuard (if needed)**: If the ``wg`` command-line tool is not installed, run ``wireguard install-wg`` to install it on Debian-based systems (like Ubuntu).
2.  **Generate Keys**: Use ``wireguard genkey`` to create private/public key pairs for the server and each client.
3.  **Configure**: Fill in the ``server_settings.py`` and ``client_settings.py`` files (located under the user config directory above) with the generated keys and your desired network settings.
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

View the path to, edit, or print the configuration files for the server or client.

If no option is provided, ``--edit`` is assumed by default.

**Options**:

- ``--path``: Print the absolute path to the config file and exit (no file creation).
- ``--edit``: Ensure the file exists (bootstrap from example if missing) and open it in your default editor (from ``$EDITOR`` or ``nano``).
- ``--cat``: Ensure the file exists (bootstrap from example if missing) and print its contents to stdout.

**Usage**::

    # Server config
    wireguard config server --path
    wireguard config server --edit
    wireguard config server --cat

    # Client config
    wireguard config client --path
    wireguard config client --edit
    wireguard config client --cat

restart
~~~~~~~

Restart the service by stopping it and then starting it again.

**Usage**::

    wireguard server restart
    wireguard client restart

check-ip (client)
~~~~~~~~~~~~~~~~~

Check the host's public IP to verify whether traffic is routed through the VPN.

**Usage**::

    wireguard client check-ip
