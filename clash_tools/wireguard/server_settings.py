"""WireGuard Server Configuration."""

SERVER_CONFIG = {
    # WireGuard server interface settings
    "INTERFACE": {
        # The server's private key.
        "private_key": "",
        # The server's IP address and subnet within the VPN.
        "address": "10.0.0.1/24",
        # The UDP port the WireGuard service will listen on.
        "listen_port": 51820,
    },
    # List of allowed clients (peers).
    "PEERS": [
        {
            # The client's public key.
            "public_key": "",
            # The VPN IP address assigned to this client.
            "allowed_ips": "10.0.0.2/32",
        },
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
