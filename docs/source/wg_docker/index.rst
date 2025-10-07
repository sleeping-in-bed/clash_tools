`wg_docker` - WireGuard Docker Orchestration
============================================

Overview
--------

``wg_docker`` is a Typer-based CLI for managing WireGuard server/client deployments via Docker. It renders configuration files from templates and controls lifecycle with docker compose. The tool is designed to be safe for first-time usage by bootstrapping missing keys and templates.

Prerequisites
-------------

- Linux host with Docker and docker compose available
- ``wg`` binary available in ``$PATH`` (used for key generation)
- Systemd-based distributions are recommended for production

Configuration Directory
-----------------------

All generated and user-managed files live under::

    /var/lib/clash_tools/wireguard

Set ``CLASH_TOOLS_WG_CONFIG_DIR`` to override the default location if you
need a custom path (for example, when running without elevated privileges).

Key files:

- ``server_config.yml``: Authoritative server-side configuration (auto-copied from packaged template on first use)
- ``server_wg0.conf``: Rendered WireGuard server config
- ``server_compose.yml``: Rendered docker compose for the server
- ``client_wg0.conf``: Rendered WireGuard client config
- ``client_compose.yml``: Rendered docker compose for the client
- ``wg_keys.json``: Pre-generated key pairs store (peer id 1 = server; 2..254 = clients)

Keys and Identity
-----------------

On first import/run, the tool ensures a keystore exists and, if missing, generates pairs for ids 1..254 using the system ``wg`` binary.

- ID 1: server private/public key
- IDs 2..254: client private/public keys
- Stored at ``wg_keys.json`` within the user config directory

Command Groups and Commands
---------------------------

server
^^^^^^

``server up``
  - Renders ``server_wg0.conf`` and ``server_compose.yml`` to the user config directory
  - Starts the server docker stack in detached mode

``server down``
  - Stops the stack and removes volumes (``down -v``)

``server restart``
  - Equivalent to ``down`` followed by ``up``

``server show``
  - Executes ``wg show`` inside the running container for inspection

``server config``
  - Manage ``server_config.yml`` with options:
    - ``--edit``: Open file in ``$VISUAL``/``$EDITOR`` (fallback to ``nano``)
    - ``--cat``: Print contents
    - ``--path``: Print absolute path
    - ``--reset``: Overwrite with packaged template

``server get-client-config <client_id>``
  - Render and print the specific client's ``client_wg0.conf`` to stdout (does not start any container)

client
^^^^^^

``client up``
  - Renders ``client_compose.yml`` and starts the client docker stack in detached mode

``client down``
  - Stops the stack and removes volumes

``client restart``
  - Equivalent to ``down`` followed by ``up``

``client config``
  - Manage ``client_wg0.conf`` with options ``--edit``/``--cat``/``--path``/``--reset``

Quick Start
-----------

::

    # Install
    pip install clash_tools

    # Start the server (missing keys and template will be auto-bootstrapped)
    python -m clash_tools.wg_docker.cli server up

    # Inspect WireGuard state in the server container
    python -m clash_tools.wg_docker.cli server show

    # Render and display the config for client id 2
    python -m clash_tools.wg_docker.cli server get-client-config 2

    # Start the client stack
    python -m clash_tools.wg_docker.cli client up

`server_config.yml` Schema
--------------------------

Top-level keys:

- ``server``:
  - ``nic`` (str): Outbound interface for MASQUERADE rules (default ``eth0``)
  - ``server_ip`` (str): Public IP or DNS name for server endpoint
  - ``subnet`` (str): Server-side IPv4 subnet in CIDR notation (e.g., ``10.9.0.0/24``)
  - ``listen_port`` (int): UDP port for the server

- ``clients`` (dict[int, client]) — keys are client ids 2..254. Each client has:
  - ``nic`` (str): Host interface used by client for LAN routes in PostUp/PreDown
  - ``exclude_defaults`` (bool): Whether to merge default private/link-local ranges into ``excludedips``
  - ``allowedips`` (list/str): Values rendered into client ``AllowedIPs`` (default ``["0.0.0.0/0"]``)
  - ``excludedips`` (list/str): CIDRs or addresses routed outside the tunnel
  - ``snat`` (bool): Whether server applies SNAT for traffic destined to this client
  - ``c_to_s_ports`` (list): Per-entry format ``[client_port, server_port, [tsl_method]]`` where ``tsl_method`` is ``tcp`` or ``udp`` (defaults to ``tcp``)

Example:

.. code-block:: yaml

    server:
      nic: eth0
      server_ip: 6.6.6.6
      subnet: 10.9.0.0/24
      listen_port: 51820

    clients:
      2:
        nic: eth0
        exclude_defaults: true
        allowedips:
          - 0.0.0.0/0
        excludedips: []
        snat: false
        c_to_s_ports:
          - [22, 2222]
          - [80, 8080]
          - [443, 8443]
      3:
        nic: eth0
        exclude_defaults: true
        allowedips:
          - 0.0.0.0/0
        excludedips: []
        snat: true
        c_to_s_ports:
          - [12345, 45678, "udp"]

Routing Behavior (Client)
-------------------------

The client template sets ``PostUp`` and ``PreDown`` commands to preserve reachability:

- Always adds a specific route for the WireGuard subnet via ``wg0``
- If ``excludedips`` (possibly merged with ``exclude_defaults``) is non-empty, routes those destinations via the client's ``nic`` and default gateway when available

Port Forwarding and Compose Ports (Server)
------------------------------------------

- For each client mapping in ``c_to_s_ports``, two things happen:
  1. iptables PREROUTING/ FORWARD rules are emitted to DNAT and ACCEPT traffic destined to ``server_port`` towards the client's ``client_port`` and IP
  2. The server compose file exposes a host port mapping ``server_port/server_protocol``

Generated Files and Templates
-----------------------------

- Templates (shipped): ``server_wg0.conf.j2``, ``client_wg0.conf.j2``, ``server_compose.yml.j2``, ``client_compose.yml.j2``
- Outputs (rendered in user config dir): ``server_wg0.conf``, ``client_wg0.conf``, ``server_compose.yml``, ``client_compose.yml``

Practical Examples
------------------

Edit server configuration in your editor::

    python -m clash_tools.wg_docker.cli server config --edit

Print absolute path to the server configuration::

    python -m clash_tools.wg_docker.cli server config --path

Reset the server configuration from the packaged template::

    python -m clash_tools.wg_docker.cli server config --reset

Render and write the client 5 config to disk::

    python -m clash_tools.wg_docker.cli server get-client-config 5 > ~/client5-wg0.conf

Troubleshooting
---------------

- ``wg`` missing: Install WireGuard tools (e.g., ``apt install wireguard``) to enable key generation
- Docker issues: Verify Docker service and compose functionality
- Port collision: Ensure ``listen_port`` and any forwarded ``server_port`` values are not already used on the host
- Firewall: Confirm that host firewall permits UDP ``listen_port`` and any forwarded TCP/UDP ports
- Logs: Use ``docker compose -f $(python -m clash_tools.wg_docker.cli server config --path | sed 's/server_config.yml/server_compose.yml/') logs | cat`` to inspect runtime logs

Security Notes
--------------

- Keep ``wg_keys.json`` secured; it contains private keys
- Review ``excludedips`` and ``allowedips`` to avoid unintentionally leaking traffic
- Validate ``server_ip`` and exposed ports before deploying to the public Internet
