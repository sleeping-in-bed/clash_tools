"""WireGuard Client Configuration."""

CLIENT_CONFIG = {
    # Client interface settings
    "INTERFACE": {
        # The client's private key.
        "private_key": "",
        # The client's IP address within the VPN.
        "address": "10.0.0.2/24",
        # The DNS server to use when connected to the VPN.
        "dns": "8.8.8.8",
    },
    # Peer (server) settings
    "PEER": {
        # The server's public key.
        "public_key": "",
        # The server's public IP address and listening port, for example: 127.0.0.1:51820
        "endpoint": "",
        # IPs to route through the VPN. 0.0.0.0/0 means all traffic.
        "allowed_ips": "0.0.0.0/0",
        # Keepalive interval in seconds to maintain NAT connection.
        "persistent_keepalive": 25,
    },
}
