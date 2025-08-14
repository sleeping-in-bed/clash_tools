"""Pydantic models for WireGuard key storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

if TYPE_CHECKING:
    from collections.abc import Sequence


class WGKeyPair(BaseModel):
    """WireGuard key pair model.

    Attributes:
        private_key: Base64-encoded WireGuard private key.
        public_key: Base64-encoded WireGuard public key derived from the private key.

    """

    private_key: str
    public_key: str


class WGKeyStore(BaseModel):
    """Key store mapping peer id to its key pair.

    Attributes:
        pairs: Mapping from peer id to its key pair. The convention is that
            peer id 1 represents the server; ids 2..254 are clients.

    """

    pairs: dict[int, WGKeyPair]


class WGPeer(BaseModel):
    """Peer render model used by templates.

    Attributes:
        public_key: Peer WireGuard public key.
        ip: Peer IPv4 address without CIDR suffix (e.g., 10.0.0.2).

    """

    public_key: str
    ip: str


TSLMethod = Literal["tcp", "udp"]


class PortMapping(BaseModel):
    """Client-to-server port mapping configuration.

    Attributes:
        client_port: Destination port on the client host.
        server_port: Exposed port on the server (external) side.
        tsl_method: Transport protocol for the mapping, either "tcp" or "udp".

    """

    client_port: int = Field(..., description="Destination port on the client host")
    server_port: int = Field(
        ...,
        description="Exposed port on the server (external) side",
    )
    tsl_method: TSLMethod = Field(
        default="tcp",
        description="Transport protocol for the mapping: 'tcp' or 'udp'",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_from_sequence(cls, data: Any) -> Any:
        """Allow sequence input like [client_port, server_port, [tsl_method]]."""
        if isinstance(data, list | tuple):
            seq: Sequence[Any] = data
            if len(seq) not in (2, 3):
                msg = "c_to_s_ports item must have 2 or 3 elements"
                raise ValueError(msg)
            client_port, server_port = int(seq[0]), int(seq[1])
            tsl_method: TSLMethod = "tcp"
            if len(seq) == 3 and seq[2] is not None:
                method = str(seq[2]).lower()
                if method not in ("tcp", "udp"):
                    msg = "tsl_method must be 'tcp' or 'udp'"
                    raise ValueError(msg)
                tsl_method = method  # type: ignore[assignment]
            return {
                "client_port": client_port,
                "server_port": server_port,
                "tsl_method": tsl_method,
            }
        return data


class ClientConfig(BaseModel):
    """Per-client configuration.

    Attributes:
        snat: Whether to apply SNAT for traffic to this client (adds POSTROUTING rules).
        c_to_s_ports: List of client-to-server port mappings as
            [client_port, server_port, optional protocol].

    """

    snat: bool = False
    c_to_s_ports: list[PortMapping] = Field(default_factory=list)


class ServerConfig(BaseModel):
    """Server configuration settings.

    Attributes:
        server_ip: Public IP or DNS name for the WireGuard server endpoint.
        subnet: Server-side IPv4 subnet in CIDR notation (e.g., 10.0.0.0/24).
        listen_port: WireGuard UDP listen port for the server.

    """

    server_ip: str
    subnet: str
    listen_port: int
    nic: str = "eth0"


class ServerWGConfig(BaseModel):
    """Top-level server configuration model.

    Attributes:
        server: Top-level server configuration.
        clients: Per-client configuration mapped by client id (2..254).

    """

    server: ServerConfig
    clients: dict[int, ClientConfig]


class ClientWGConfig(BaseModel):
    """Client-side configuration file (client_config.yml).

    Attributes:
        client_ip: VPN address for the client (without CIDR suffix or with, per usage).
        privatekey: WireGuard private key for the client.
        publickey: WireGuard public key for the server.
        endpoint: Server endpoint in the format "host:port".
        allowedips: Allowed IPs routes for the peer (list of CIDRs or addresses).
        excludedips: IPs to exclude/bypass from routing (list of CIDRs).

    """

    client_ip: str
    privatekey: str
    publickey: str
    endpoint: str
    allowedips: list[str]
    excludedips: list[str] = Field(default_factory=list)
    nic: str = "eth0"

    @field_validator("excludedips", mode="before")
    @classmethod
    def _accept_none_excludedips(cls, v):
        """Allow null/None excludedips by coercing to an empty list."""
        return [] if v is None else v
