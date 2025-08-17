"""WireGuard utilities.

Provide helpers to generate WireGuard key pairs via the system `wg` binary,
manage a JSON store of pairs, and resolve config directories.
"""

from __future__ import annotations

import json
from ipaddress import IPv4Address, IPv4Network, ip_network
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run
from typing import Final

from .config import (
    get_jinja_env,
    get_user_config_dir,
    load_server_config,
)
from .models import ClientConfig, WGKeyPair, WGKeyStore, WGPeer

_WG_BIN: Final[str] = "wg"


def generate_wg_keypair() -> WGKeyPair:
    """Generate a WireGuard key pair using the `wg` command.

    Returns:
        WGKeyPair: Pydantic model containing `private_key` and `public_key`.

    Raises:
        RuntimeError: If the `wg` binary is not available or commands fail.

    """
    try:
        genkey_proc: CompletedProcess[str] = run(  # noqa: S603
            [_WG_BIN, "genkey"],
            check=True,
            capture_output=True,
            text=True,
        )
        private_key: str = genkey_proc.stdout.strip()

        pubkey_proc: CompletedProcess[str] = run(  # noqa: S603
            [_WG_BIN, "pubkey"],
            input=private_key,
            check=True,
            capture_output=True,
            text=True,
        )
        public_key: str = pubkey_proc.stdout.strip()
    except (FileNotFoundError, CalledProcessError) as exc:
        msg = "wg keygen failed"
        raise RuntimeError(msg) from exc

    return WGKeyPair(private_key=private_key, public_key=public_key)


class WGKeyStoreManager:
    """Manage generation and persistence of WireGuard key pairs in JSON.

    The JSON structure conforms to `WGKeyStore`.
    """

    def __init__(self) -> None:
        self.json_path: Path = get_user_config_dir() / "wg_keys.json"

    def generate_pairs_for_range(self, start: int = 1, end: int = 254) -> WGKeyStore:
        """Generate key pairs for ids in the inclusive range [start, end].

        Args:
            start: Starting id, default 1.
            end: Ending id, default 254.

        Returns:
            WGKeyStore: Mapping from id to key pair.

        Raises:
            ValueError: If the range is invalid.

        """
        if start < 1 or end > 254 or start > end:
            msg = "Invalid range; must satisfy 1 <= start <= end <= 254"
            raise ValueError(msg)

        pairs: dict[int, WGKeyPair] = {}
        for peer_id in range(start, end + 1):
            pairs[peer_id] = generate_wg_keypair()

        return WGKeyStore(pairs=pairs)

    def write_store(self, store: WGKeyStore) -> None:
        """Write the given store to the configured JSON file."""
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        # Use Pydantic's dict for serialization, preserving keys as strings in JSON
        with self.json_path.open("w", encoding="utf-8") as f:
            json.dump(store.model_dump(), f, indent=2, ensure_ascii=False)

    def read_store(self) -> WGKeyStore:
        """Read the JSON file and return a `WGKeyStore` instance.

        If the file does not exist, an empty structure is returned.
        """
        if not self.json_path.exists():
            return WGKeyStore(pairs={})
        with self.json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return WGKeyStore(**data)


class WGConfRenderer:
    """Renderer for server wg0.conf and iptables PostUp/PostDown rules.

    Initializes with a key store manager and loads `config.yaml` from the
    user config directory by default. The server subnet and listen port are
    taken from the loaded configuration unless explicitly overridden.
    """

    def __init__(self) -> None:
        self.store: WGKeyStore = WGKeyStoreManager().read_store()
        self.server_cfg = load_server_config()

        self.cidr: str = self.server_cfg.server.subnet
        self.listen_port: int = self.server_cfg.server.listen_port

        # Shared network fields
        self.network: IPv4Network = ip_network(self.cidr, strict=False)  # type: ignore[assignment]
        self.base_ip: IPv4Address = self.network.network_address
        self.server_ip: IPv4Address = IPv4Address(int(self.base_ip) + 1)

    def _build_server_post(self) -> tuple[list[str], list[str]]:
        """Build server PostUp and PostDown iptables rules from loaded config.

        Returns:
            Tuple of (post_up_rules, post_down_rules).

        """
        post_up_rules: list[str] = [
            "iptables -A FORWARD -i %i -j ACCEPT",
            f"iptables -t nat -A POSTROUTING -o {self.server_cfg.server.nic} -j MASQUERADE",
        ]
        post_down_rules: list[str] = [
            "iptables -D FORWARD -i %i -j ACCEPT",
            f"iptables -t nat -D POSTROUTING -o {self.server_cfg.server.nic} -j MASQUERADE",
        ]

        for peer_id, client_cfg in sorted(self.server_cfg.clients.items()):
            client_ip = IPv4Address(int(self.base_ip) + int(peer_id))
            if client_ip not in self.network:
                continue
            for mapping in client_cfg.c_to_s_ports:
                up_dnat = (
                    f"iptables -t nat -A PREROUTING -p {mapping.tsl_method} --dport {mapping.server_port} "
                    f"-j DNAT --to-destination {client_ip!s}:{mapping.client_port}"
                )
                up_forward = (
                    f"iptables -A FORWARD -p {mapping.tsl_method} -d {client_ip!s} "
                    f"--dport {mapping.client_port} -j ACCEPT"
                )
                post_up_rules.extend([up_dnat, up_forward])

                down_dnat = (
                    f"iptables -t nat -D PREROUTING -p {mapping.tsl_method} --dport {mapping.server_port} "
                    f"-j DNAT --to-destination {client_ip!s}:{mapping.client_port}"
                )
                down_forward = (
                    f"iptables -D FORWARD -p {mapping.tsl_method} -d {client_ip!s} "
                    f"--dport {mapping.client_port} -j ACCEPT"
                )
                post_down_rules.extend([down_dnat, down_forward])

                if client_cfg.snat:
                    up_snat = (
                        f"iptables -t nat -A POSTROUTING -o wg0 -p {mapping.tsl_method} -d {client_ip!s} "
                        f"--dport {mapping.client_port} -j SNAT --to-source {self.server_ip!s}"
                    )
                    down_snat = (
                        f"iptables -t nat -D POSTROUTING -o wg0 -p {mapping.tsl_method} -d {client_ip!s} "
                        f"--dport {mapping.client_port} -j SNAT --to-source {self.server_ip!s}"
                    )
                    post_up_rules.append(up_snat)
                    post_down_rules.append(down_snat)

        return post_up_rules, post_down_rules

    def render_server_conf(self, write: bool = True) -> tuple[str, Path]:
        """Render full wg0.conf with PostUp/PostDown from the template."""
        server_private_key: str = ""
        peers: list[WGPeer] = []
        # Server private key from id=1
        if 1 in self.store.pairs:
            server_private_key = self.store.pairs[1].private_key

        # Render peers only for clients defined in server_cfg
        for peer_id in sorted(self.server_cfg.clients.keys()):
            if peer_id == 1:
                continue
            pair = self.store.pairs.get(peer_id)
            if pair is None:
                continue
            candidate_ip = IPv4Address(int(self.base_ip) + int(peer_id))
            if candidate_ip not in self.network:
                continue
            peers.append(WGPeer(public_key=pair.public_key, ip=str(candidate_ip)))

        post_up_rules, post_down_rules = self._build_server_post()

        template = get_jinja_env().get_template("server_wg0.conf.j2")
        rendered: str = template.render(
            server_ip=str(self.server_ip),
            listen_port=self.listen_port,
            server_private_key=server_private_key,
            peers=peers,
            post_up_rules=post_up_rules,
            post_down_rules=post_down_rules,
        )
        out_path = get_user_config_dir() / "server_wg0.conf"
        if write:
            out_path.write_text(rendered, encoding="utf-8")
        return rendered, out_path

    def _build_client_post(self, client_cfg: ClientConfig) -> tuple[str, str]:
        """Build client PostUp and PreDown route commands from server-side client cfg.

        Ensures the WireGuard subnet stays reachable by adding a specific
        route via `wg0`, even if LAN ranges are excluded.
        """
        post_up_cmds: list[str] = [f'ip route replace "{self.cidr}" dev wg0 || true']
        pre_down_cmds: list[str] = [f'ip route del "{self.cidr}" || true']

        if client_cfg.excludedips:
            dsts = " ".join(sorted(client_cfg.excludedips))
            # Extract default gateway IP only if a 'via' exists; otherwise leave empty
            post_up_cmds.insert(
                0,
                "gw=$(ip route show default | awk '{for(i=1;i<=NF;i++) if($i==\"via\"){print $(i+1); exit}}')",
            )
            post_up_cmds.append(
                f'for dst in {dsts}; do if [ -n "$gw" ]; then ip route replace "$dst" via "$gw" dev {client_cfg.nic} || true; else ip route replace "$dst" dev {client_cfg.nic} || true; fi; done',
            )
            pre_down_cmds.append(
                f'for dst in {dsts}; do ip route del "$dst" || true; done',
            )

        post_up = 'sh -c "' + "; ".join(post_up_cmds) + '"'
        pre_down = 'sh -c "' + "; ".join(pre_down_cmds) + '"'
        return post_up, pre_down

    def render_client_conf(
        self,
        client_id: int,
        write: bool = True,
    ) -> tuple[str, Path]:
        """Render client wg0.conf for a given client_id from server_config.yml.

        Args:
            client_id: Client id (host part) used to derive client_ip and keys.
            write: Whether to write the rendered file to user config dir.

        Returns:
            Tuple of (rendered_text, output_path).

        """
        client_cfg = self.server_cfg.clients.get(client_id)
        if client_cfg is None:
            msg = f"client id {client_id} not found in server config"
            raise RuntimeError(msg)

        # Resolve keys
        server_public_key: str | None = None
        client_private_key: str | None = None
        for peer_id, pair in self.store.pairs.items():
            if peer_id == 1:
                server_public_key = pair.public_key
            if peer_id == client_id:
                client_private_key = pair.private_key
        if server_public_key is None or client_private_key is None:
            msg = "missing keys for client rendering"
            raise RuntimeError(msg)

        client_ip = str(IPv4Address(int(self.base_ip) + client_id))
        endpoint = f"{self.server_cfg.server.server_ip}:{self.listen_port}"

        template = get_jinja_env().get_template("client_wg0.conf.j2")
        post_up, pre_down = self._build_client_post(client_cfg)
        rendered: str = template.render(
            client_ip=client_ip,
            client_private_key=client_private_key,
            server_public_key=server_public_key,
            allowed_ips=",".join(sorted(client_cfg.allowedips)),
            endpoint=endpoint,
            post_up=post_up,
            pre_down=pre_down,
        )
        out_path = get_user_config_dir() / "client_wg0.conf"
        if write:
            out_path.write_text(rendered, encoding="utf-8")
        return rendered, out_path

    def render_client_compose(self, write: bool = True) -> tuple[str, Path]:
        """Render docker compose for client deployment."""
        template = get_jinja_env().get_template("client_compose.yml.j2")
        rendered = template.render()
        out_path = get_user_config_dir() / "client_compose.yml"
        if write:
            out_path.write_text(rendered, encoding="utf-8")
        return rendered, out_path

    def render_server_compose(self, write: bool = True) -> tuple[str, Path]:
        """Render docker compose for server deployment with dynamic ports."""
        # Build forwards from user cfg
        forwards: list[dict[str, str | int]] = []
        for peer_id, client_cfg in sorted(self.server_cfg.clients.items()):
            client_ip = IPv4Address(int(self.base_ip) + int(peer_id))
            for mapping in client_cfg.c_to_s_ports:
                forwards.append(
                    {
                        "tsl_method": mapping.tsl_method,
                        "server_port": mapping.server_port,
                        "client_ip": str(client_ip),
                        "client_port": mapping.client_port,
                    },
                )
        template = get_jinja_env().get_template("server_compose.yml.j2")
        rendered = template.render(listen_port=self.listen_port, forwards=forwards)
        out_path = get_user_config_dir() / "server_compose.yml"
        if write:
            out_path.write_text(rendered, encoding="utf-8")
        return rendered, out_path
