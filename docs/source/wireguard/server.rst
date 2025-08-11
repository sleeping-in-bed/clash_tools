Server Management
=================

The ``wireguard server`` command group is used to manage the WireGuard server instance. It handles configuration generation and service lifecycle.

Configuration files are stored under the user's config directory following the XDG Base Directory rules:

- If ``XDG_CONFIG_HOME`` is set: ``$XDG_CONFIG_HOME/clash_tools/wireguard/server_settings.py``
- Otherwise: ``~/.config/clash_tools/wireguard/server_settings.py``

Commands
--------

server up
~~~~~~~~~

Generates the ``server_wg0.conf`` and ``server_compose.yml`` files based on ``server_settings.py`` and then starts the Docker Compose service in detached mode.

**Usage**::

    wireguard server up

server down
~~~~~~~~~~~

Stops and removes the containers defined in ``server_compose.yml``.

**Usage**::

    wireguard server down

server restart
~~~~~~~~~~~~~~

Stops the server if running and then starts it again (equivalent to ``down`` followed by ``up``).

**Usage**::

    wireguard server restart

Configuration (`server_settings.py`)
------------------------------------

This file contains all the necessary settings for the WireGuard server. You must fill in the required values before starting the service. On first use, the tool will bootstrap this file from an example into your user config directory if it does not exist.

.. code-block:: python

    """
    WireGuard Server Configuration
    """

    SERVER_CONFIG = {
        # WireGuard server interface settings
        "INTERFACE": {
            # The server's private key.
            # Generate with: wireguard genkey
            "private_key": "SERVER_PRIVATE_KEY",
            # The server's IP address and subnet within the VPN.
            "address": "10.0.0.1/24",
            # The UDP port the WireGuard service will listen on.
            "listen_port": 51820,
        },
        # List of allowed clients (peers).
        "PEERS": [
            {
                # The client's public key.
                "public_key": "CLIENT_PUBLIC_KEY",
                # The VPN IP address assigned to this client.
                "allowed_ips": "10.0.0.2/32",
            },
            # Add more clients here if needed
        ],
        # Port forwarding rules.
        "FORWARDS": [
            {
                "protocol": "tcp",
                "external_port": 2222,
                "internal_ip": "10.0.0.2",
                "internal_port": 22,
            },
            {
                "protocol": "tcp",
                "external_port": 8080,
                "internal_ip": "10.0.0.2",
                "internal_port": 80,
            },
        ],
    }

**Parameter Details**:

- **INTERFACE**:
    - ``private_key``: **(Required)** The server's unique private key.
    - ``address``: The virtual IP address of the server inside the VPN.
    - ``listen_port``: The public-facing UDP port for WireGuard traffic. Ensure this port is open on your firewall.
- **PEERS**:
    - ``public_key``: **(Required)** The public key of an allowed client.
    - ``allowed_ips``: The internal VPN IP address assigned to this client.
- **FORWARDS**:
    - A list of port forwarding rules. The server will use ``iptables`` to forward traffic from a public ``external_port`` to a client's ``internal_ip:internal_port``. This is optional.
