Client Management
=================

The ``wireguard client`` command group manages the WireGuard client instance, which connects to the server.

Commands
--------

client up
~~~~~~~~~

Generates the ``client_wg0.conf`` and ``client_compose.yml`` files from ``client_settings.py`` and starts the Docker Compose service.

**Usage**::

    wireguard client up

client down
~~~~~~~~~~~

Stops and removes the client's Docker Compose service.

**Usage**::

    wireguard client down

Configuration (`client_settings.py`)
------------------------------------

This file contains the settings needed to connect to the WireGuard server.

.. code-block:: python

    """
    WireGuard Client Configuration
    """

    CLIENT_CONFIG = {
        # Client interface settings
        "INTERFACE": {
            # The client's private key.
            # Generate with: wireguard genkey
            "private_key": "CLIENT_PRIVATE_KEY",
            # The client's IP address within the VPN. Must match what's in server_settings.py.
            "address": "10.0.0.2/24",
            # The DNS server to use when connected to the VPN.
            "dns": "8.8.8.8",
        },
        # Peer (server) settings
        "PEER": {
            # The server's public key.
            "public_key": "SERVER_PUBLIC_KEY",
            # The server's public IP address and listening port.
            # Example: "your_server_ip:51820"
            "endpoint": "SERVER_PUBLIC_IP:PORT",
            # IPs to route through the VPN. 0.0.0.0/0 means all traffic.
            "allowed_ips": "0.0.0.0/0",
            # Keepalive interval in seconds to maintain NAT connection.
            "persistent_keepalive": 25,
        },
    }

**Parameter Details**:

- **INTERFACE**:
    - ``private_key``: **(Required)** The client's unique private key.
    - ``address``: The virtual IP assigned to this client. This should correspond to an IP listed in the server's ``PEERS`` configuration.
    - ``dns``: The DNS server to be used by the client when the VPN is active.
- **PEER**:
    - ``public_key``: **(Required)** The public key of the server.
    - ``endpoint``: **(Required)** The public IP address and port of the WireGuard server.
    - ``allowed_ips``: Defines which traffic should be routed through the VPN. ``0.0.0.0/0`` routes all traffic.
    - ``persistent_keepalive``: Helps maintain the connection through NAT firewalls.
