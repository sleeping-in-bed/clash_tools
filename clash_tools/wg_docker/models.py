"""Pydantic models for WireGuard key storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, cast

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
                tsl_method = cast("TSLMethod", method)
            return {
                "client_port": client_port,
                "server_port": server_port,
                "tsl_method": tsl_method,
            }
        return data


class ClientConfig(BaseModel):
    """Per-client configuration (authoritative for client wg0 rendering).

    Attributes:
        nic: Host interface name used for local LAN routes in client PostUp/PreDown.
        exclude_defaults: Whether to include common private/link-local ranges in
            `excludedips` by default. When true, the following ranges are merged
            into `excludedips` if not present: 10.0.0.0/8, 172.16.0.0/12,
            192.168.0.0/16, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16.
        allowedips: Set of CIDRs/addresses for the client peer's AllowedIPs.
        excludedips: Set of CIDRs/addresses to bypass the tunnel (routed via `nic`).
        snat: Whether the server should apply SNAT for traffic destined to this client.
        c_to_s_ports: List of client-to-server port mappings as
            [client_port, server_port, optional protocol], where protocol is
            "tcp" or "udp" (defaults to "tcp").

    """

    nic: str = "eth0"
    exclude_defaults: bool = True
    allowedips: set[str] = Field(default_factory=lambda: {"0.0.0.0/0"})
    excludedips: set[str] = Field(default_factory=set)
    snat: bool = False
    c_to_s_ports: list[PortMapping] = Field(default_factory=list)

    @field_validator("c_to_s_ports", mode="before")
    @classmethod
    def _accept_none_c_to_s_ports(cls, v: Any) -> Any:
        """Allow null/None c_to_s_ports by coercing to an empty list."""
        return [] if v is None else v

    @field_validator("allowedips", "excludedips", mode="before")
    @classmethod
    def _lists_allow_none(cls, v: Any) -> Any:
        """Allow None and coerce to set; accept list/str as set."""
        if v is None:
            return set()
        if isinstance(v, str):
            return {v}
        if isinstance(v, list | tuple | set):
            return set(v)
        return v

    @model_validator(mode="after")
    def _apply_default_excluded(self) -> ClientConfig:
        """Merge default excluded ranges when enabled."""
        default_excluded: set[str] = {
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
            "100.64.0.0/10",
            "127.0.0.0/8",
            "169.254.0.0/16",
        }
        if self.exclude_defaults:
            self.excludedips = set(self.excludedips) | default_excluded
        # Ensure allowedips/excludedips are sets (in case upstream coercion missed)
        self.allowedips = set(self.allowedips)
        self.excludedips = set(self.excludedips)
        return self


class ServerConfig(BaseModel):
    """Server configuration settings.

    Attributes:
        nic: Outbound interface name used for server-side MASQUERADE rules.
        server_ip: Public IP or DNS name for the WireGuard server endpoint.
        subnet: Server-side IPv4 subnet in CIDR notation (e.g., 10.0.0.0/24).
        listen_port: WireGuard UDP listen port for the server.

    """

    nic: str = "eth0"
    server_ip: str
    subnet: str
    listen_port: int


class ServerWGConfig(BaseModel):
    """Top-level server configuration model.

    Attributes:
        server: Top-level server configuration.
        clients: Per-client configuration mapped by client id (2..254).

    """

    server: ServerConfig
    clients: dict[int, ClientConfig]
