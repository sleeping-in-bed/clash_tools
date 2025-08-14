#!/usr/bin/env python
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

# Base path definitions
BASE_DIR = Path(__file__).parent.resolve()
TEMPLATE_DIR = BASE_DIR / "templates"

# Example settings shipped with the project (used to bootstrap user config)
EXAMPLE_SERVER_SETTINGS_PATH = BASE_DIR / "server_settings.py"
EXAMPLE_CLIENT_SETTINGS_PATH = BASE_DIR / "client_settings.py"


def get_user_config_dir() -> Path:
    """Return the user config directory for this tool, respecting XDG_CONFIG_HOME."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    base_config_dir = (
        Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
    )
    return base_config_dir / "clash_tools" / "wireguard"


USER_CONFIG_DIR = get_user_config_dir()
USER_SERVER_SETTINGS_PATH = USER_CONFIG_DIR / "server_settings.py"
USER_CLIENT_SETTINGS_PATH = USER_CONFIG_DIR / "client_settings.py"

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


def render_template(template_name: str, context: dict, output_path: Path) -> None:
    """Renders a Jinja2 template and writes it to a file."""
    template = env.get_template(template_name)
    rendered_content = template.render(context)
    output_path.write_text(rendered_content, encoding="utf-8")
    click.echo(click.style(f"✓ File generated: {output_path}", fg="green"))


def load_config_var(py_path: Path, var_name: str) -> dict:
    """Load a top-level variable from a Python file located at an arbitrary path.

    Comments: Use importlib to execute the file as a module-like object and fetch the variable.
    """
    if not py_path.exists():
        msg = f"Config file not found: {py_path}"
        raise FileNotFoundError(msg)
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    if spec is None or spec.loader is None:
        msg = f"Unable to load spec for {py_path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    try:
        value = getattr(module, var_name)
    except AttributeError as exc:
        msg = f"Variable '{var_name}' not found in {py_path}"
        raise AttributeError(msg) from exc
    if not isinstance(value, dict):
        msg = f"Variable '{var_name}' in {py_path} must be a dict"
        raise TypeError(msg)
    return value


def run_compose_command(command: str, compose_file_name: str) -> None:
    """Runs a docker-compose command using a specific compose file."""
    compose_file_path = BASE_DIR / compose_file_name
    if not compose_file_path.exists():
        click.echo(
            click.style(f"❌ Compose file not found: {compose_file_path}", fg="red"),
            err=True,
        )
        return

    base_command = ["docker", "compose", "-f", str(compose_file_path)]
    full_command = base_command + (["up", "-d"] if command == "up" else [command])

    try:
        subprocess.run(full_command, check=True, cwd=BASE_DIR)
        status = "started" if command == "up" else "stopped"
        click.echo(click.style(f"\n🎉 Service {status} successfully!", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo(
            click.style(f"\n❌ Failed to {command} service: {e}", fg="red"),
            err=True,
        )
    except FileNotFoundError:
        click.echo(
            click.style(
                "\n❌ Command failed. Please ensure Docker and Docker Compose are installed.",
                fg="red",
            ),
            err=True,
        )


def generate_server_iptables_rules(server_config: dict) -> tuple[list[str], list[str]]:
    """Generates iptables rules for the server."""
    forwards = server_config.get("FORWARDS", [])
    post_up_rules = [
        "iptables -A FORWARD -i %i -j ACCEPT",
        "iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
    ]
    post_down_rules = [
        "iptables -D FORWARD -i %i -j ACCEPT",
        "iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE",
    ]

    for rule in forwards:
        up_dnat = f"iptables -t nat -A PREROUTING -p {rule['protocol']} --dport {rule['external_port']} -j DNAT --to-destination {rule['internal_ip']}:{rule['internal_port']}"
        up_forward = f"iptables -A FORWARD -p {rule['protocol']} -d {rule['internal_ip']} --dport {rule['internal_port']} -j ACCEPT"
        post_up_rules.extend([up_dnat, up_forward])

        down_dnat = f"iptables -t nat -D PREROUTING -p {rule['protocol']} --dport {rule['external_port']} -j DNAT --to-destination {rule['internal_ip']}:{rule['internal_port']}"
        down_forward = f"iptables -D FORWARD -p {rule['protocol']} -d {rule['internal_ip']} --dport {rule['internal_port']} -j ACCEPT"
        post_down_rules.insert(2, down_forward)
        post_down_rules.insert(2, down_dnat)

    return post_up_rules, post_down_rules


# --- Click Command Definitions ---


@click.group()
def cli() -> None:
    """A tool to manage WireGuard server and client configurations."""
    return


# --- Server Command Group ---
@cli.group()
def server() -> None:
    """Manage server configuration and services."""
    return


@server.command(name="up", help="Generate server config files and start the service.")
def server_up() -> None:
    """Generates server config files and starts the service."""
    try:
        SERVER_CONFIG = load_config_var(USER_SERVER_SETTINGS_PATH, "SERVER_CONFIG")
    except (FileNotFoundError, ImportError, AttributeError, TypeError) as e:
        message = (
            f"❌ Failed to load server config from {USER_SERVER_SETTINGS_PATH}.\n"
            "Use 'python -m clash_tools.wireguard.up config server' to create/edit it.\n"
            f"Error: {e}"
        )
        click.echo(click.style(message, fg="red"), err=True)
        return

    click.echo(
        click.style(
            "🚀 Generating server configuration files...",
            fg="cyan",
            bold=True,
        ),
    )
    post_up_rules, post_down_rules = generate_server_iptables_rules(SERVER_CONFIG)

    render_template(
        "server_wg0.conf.j2",
        {
            "interface": SERVER_CONFIG["INTERFACE"],
            "peers": SERVER_CONFIG["PEERS"],
            "post_up_rules": post_up_rules,
            "post_down_rules": post_down_rules,
        },
        BASE_DIR / "server_wg0.conf",
    )
    render_template(
        "server_compose.yml.j2",
        {
            "listen_port": SERVER_CONFIG["INTERFACE"]["listen_port"],
            "forwards": SERVER_CONFIG["FORWARDS"],
        },
        BASE_DIR / "server_compose.yml",
    )

    click.echo(click.style("\n🚀 Starting server...", fg="cyan", bold=True))
    run_compose_command("up", "server_compose.yml")


@server.command(name="down", help="Stop and remove the server service.")
def server_down() -> None:
    """Stops and removes the server service."""
    click.echo(click.style("🚀 Stopping server...", fg="cyan", bold=True))
    run_compose_command("down", "server_compose.yml")


# --- Client Command Group ---
@cli.group()
def client() -> None:
    """Manage client configuration and services."""
    return


@client.command(name="up", help="Generate client config files and start the service.")
def client_up() -> None:
    """Generates client config files and starts the service."""
    try:
        CLIENT_CONFIG = load_config_var(USER_CLIENT_SETTINGS_PATH, "CLIENT_CONFIG")
    except (FileNotFoundError, ImportError, AttributeError, TypeError) as e:
        message = (
            f"❌ Failed to load client config from {USER_CLIENT_SETTINGS_PATH}.\n"
            "Use 'python -m clash_tools.wireguard.up config client' to create/edit it.\n"
            f"Error: {e}"
        )
        click.echo(click.style(message, fg="red"), err=True)
        return

    click.echo(
        click.style(
            "🚀 Generating client configuration files...",
            fg="cyan",
            bold=True,
        ),
    )
    render_template(
        "client_wg0.conf.j2",
        {
            "interface": CLIENT_CONFIG["INTERFACE"],
            "peer": CLIENT_CONFIG["PEER"],
        },
        BASE_DIR / "client_wg0.conf",
    )
    render_template("client_compose.yml.j2", {}, BASE_DIR / "client_compose.yml")

    click.echo(
        click.style(
            "\n🔧 Applying required kernel setting 'net.ipv4.conf.all.src_valid_mark=1' (requires sudo)...",
            fg="cyan",
            bold=True,
        ),
    )
    try:
        sysctl_command = ["sudo", "sysctl", "-w", "net.ipv4.conf.all.src_valid_mark=1"]
        subprocess.run(sysctl_command, check=True, capture_output=True, text=True)
        click.echo(click.style("✓ Kernel setting applied successfully.", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo(
            click.style(
                f"⚠️  Warning: Could not set sysctl property. This might not be a "
                f"problem if it's already set.\n   Error: {e.stderr.strip()}",
                fg="yellow",
            ),
            err=True,
        )
    except FileNotFoundError:
        click.echo(
            click.style(
                "❌ Command 'sudo' or 'sysctl' not found. Cannot apply kernel settings. "
                "Please set 'net.ipv4.conf.all.src_valid_mark=1' manually.",
                fg="red",
            ),
            err=True,
        )

    click.echo(click.style("\n🚀 Starting client...", fg="cyan", bold=True))
    run_compose_command("up", "client_compose.yml")


@client.command(name="down", help="Stop and remove the client service.")
def client_down() -> None:
    """Stops and removes the client service."""
    click.echo(click.style("🚀 Stopping client...", fg="cyan", bold=True))
    run_compose_command("down", "client_compose.yml")


@client.command(
    name="check-ip",
    help="Check the host's public IP to verify the VPN connection.",
)
def check_ip() -> None:
    """Checks the host's public IP to see if it matches the VPN server."""
    click.echo(click.style("🔎 Checking host's public IP...", fg="cyan", bold=True))

    # 1. Get server IP from settings
    server_ip = None
    try:
        CLIENT_CONFIG = load_config_var(USER_CLIENT_SETTINGS_PATH, "CLIENT_CONFIG")
        endpoint = CLIENT_CONFIG.get("PEER", {}).get("endpoint")
        if not endpoint or ":" not in endpoint:
            click.echo(
                click.style(
                    f"❌ Invalid or missing endpoint in client_settings.py: '{endpoint}'",
                    fg="red",
                ),
                err=True,
            )
            return
        server_ip = endpoint.split(":")[0]
        click.echo(
            f"ℹ️  VPN Server IP (from settings): {click.style(server_ip, fg='blue')}",
        )
    except (FileNotFoundError, ImportError, AttributeError, TypeError) as e:
        click.echo(
            click.style(f"❌ Error reading server IP from settings: {e}", fg="red"),
            err=True,
        )
        return

    # 2. Get public IP from external services
    ip_services = ["ifconfig.me", "ip.sb"]
    public_ip = None
    click.echo(
        click.style("⏳ Querying external services to find public IP...", fg="cyan"),
    )
    for service in ip_services:
        try:
            result = subprocess.run(
                ["curl", "-s", "-4", service],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            fetched_ip = result.stdout.strip()
            # A simple sanity check for an IP address format
            if len(fetched_ip.split(".")) == 4:
                public_ip = fetched_ip
                click.echo(
                    f"   ✓ Found host public IP via {service}: {click.style(public_ip, fg='blue')}",
                )
                break
            click.echo(
                click.style(
                    f"   ⚠️ Got invalid response from {service}",
                    fg="yellow",
                ),
                err=True,
            )
        except FileNotFoundError:
            click.echo(
                click.style(
                    "❌ Command `curl` not found. Please install curl to use this feature.",
                    fg="red",
                ),
                err=True,
            )
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            click.echo(
                click.style(
                    f"   ⚠️ Failed to get IP from {service}, trying next...",
                    fg="yellow",
                ),
            )
            continue

    if not public_ip:
        click.echo(
            click.style(
                "\n❌ Failed to determine public IP after trying all available services.",
                fg="red",
            ),
            err=True,
        )
        return

    # 3. Compare and report
    click.echo("-" * 40)
    if public_ip == server_ip:
        click.echo(click.style("✅ SUCCESS!", fg="green", bold=True))
        click.echo(
            click.style(
                f"   Your public IP ({public_ip}) matches the VPN server IP.",
                fg="green",
            ),
        )
        click.echo(
            click.style(
                "   Host traffic appears to be correctly routed through the VPN.",
                fg="green",
            ),
        )
    else:
        click.echo(click.style("❌ MISMATCH!", fg="red", bold=True))
        click.echo(click.style(f"   Your public IP is {public_ip}.", fg="red"))
        click.echo(click.style(f"   The VPN server IP is {server_ip}.", fg="red"))
        click.echo(
            click.style(
                "   Host traffic is NOT being routed through the VPN.",
                fg="red",
            ),
        )
    click.echo("-" * 40)


# --- Config and Utility Command Group ---
@cli.group(
    help="View or edit configuration files. Default location: ~/.config/clash_tools/wireguard/",
)
def config() -> None:
    """Manages configuration files."""
    return


def _config_handler(
    config_file_path: Path,
    example_file_path: Path,
    show_path: bool,
    open_editor: bool,
    print_content: bool,
) -> None:
    """Generic handler for config commands.

    Comments: Provide three modes:
    - path: only print absolute path, do not modify filesystem
    - edit: ensure dir/file exist (bootstrapping from example), then open editor
    - cat: ensure dir/file exist (bootstrapping from example), then print content
    """
    # Enforce default behavior: if no explicit option, default to edit
    if not any([show_path, open_editor, print_content]):
        open_editor = True

    # When only showing path, avoid creating directories/files or extra logs
    abs_path = str(config_file_path.absolute())
    if show_path and not (open_editor or print_content):
        click.echo(abs_path)
        return

    # For edit/cat: ensure directory exists
    config_dir = config_file_path.parent
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        click.echo(click.style(f"✓ Created config directory: {config_dir}", fg="green"))

    # Bootstrap file from example if missing
    if not config_file_path.exists():
        try:
            shutil.copyfile(example_file_path, config_file_path)
            click.echo(
                click.style(
                    f"✓ Bootstrapped config from example to: {config_file_path}",
                    fg="green",
                ),
            )
        except Exception as e:
            click.echo(
                click.style(f"❌ Failed to create config file: {e}", fg="red"),
                err=True,
            )
            return

    # Edit
    if open_editor:
        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run([editor, str(config_file_path)], check=True)
        except Exception as e:
            click.echo(click.style(f"❌ Error opening editor: {e}", fg="red"), err=True)
            return

    # Cat
    if print_content:
        try:
            content = config_file_path.read_text(encoding="utf-8")
            click.echo(content)
        except Exception as e:
            click.echo(click.style(f"❌ Error reading file: {e}", fg="red"), err=True)
            return


@config.command(name="server", help="Manage the server configuration file.")
@click.option(
    "--path",
    "show_path",
    is_flag=True,
    help="Only print the config file path.",
)
@click.option(
    "--edit",
    "open_editor",
    is_flag=True,
    help="Open the server config in your editor.",
)
@click.option(
    "--cat",
    "print_content",
    is_flag=True,
    help="Print the server config content to stdout.",
)
def config_server(show_path: bool, open_editor: bool, print_content: bool) -> None:
    """Operate on the server configuration file."""
    # Reject multiple action flags
    if sum([show_path, open_editor, print_content]) > 1:
        click.echo(
            click.style(
                "❌ Please choose only one of --path / --edit / --cat.",
                fg="red",
            ),
            err=True,
        )
        return
    _config_handler(
        USER_SERVER_SETTINGS_PATH,
        EXAMPLE_SERVER_SETTINGS_PATH,
        show_path,
        open_editor,
        print_content,
    )


@config.command(name="client", help="Manage the client configuration file.")
@click.option(
    "--path",
    "show_path",
    is_flag=True,
    help="Only print the config file path.",
)
@click.option(
    "--edit",
    "open_editor",
    is_flag=True,
    help="Open the client config in your editor.",
)
@click.option(
    "--cat",
    "print_content",
    is_flag=True,
    help="Print the client config content to stdout.",
)
def config_client(show_path: bool, open_editor: bool, print_content: bool) -> None:
    """Operate on the client configuration file."""
    if sum([show_path, open_editor, print_content]) > 1:
        click.echo(
            click.style(
                "❌ Please choose only one of --path / --edit / --cat.",
                fg="red",
            ),
            err=True,
        )
        return
    _config_handler(
        USER_CLIENT_SETTINGS_PATH,
        EXAMPLE_CLIENT_SETTINGS_PATH,
        show_path,
        open_editor,
        print_content,
    )


# --- Restart Commands ---
@server.command(name="restart", help="Restart the server service (down then up).")
def server_restart() -> None:
    """Restarts the server service by stopping and then starting it."""
    click.echo(click.style("🔁 Restarting server...", fg="cyan", bold=True))
    run_compose_command("down", "server_compose.yml")
    server_up()


@client.command(name="restart", help="Restart the client service (down then up).")
def client_restart() -> None:
    """Restarts the client service by stopping and then starting it."""
    click.echo(click.style("🔁 Restarting client...", fg="cyan", bold=True))
    run_compose_command("down", "client_compose.yml")
    client_up()


@cli.command(name="install-wg", help="Install WireGuard using apt (requires sudo).")
def install_wg() -> None:
    """Installs the 'wireguard' package using apt."""
    click.echo(
        click.style(
            "🚀 This command will attempt to install WireGuard using apt.",
            fg="cyan",
        ),
    )
    click.echo(
        click.style("   You may be prompted for your sudo password.", fg="yellow"),
    )
    try:
        click.echo(click.style("\n--> Running 'sudo apt-get update'...", fg="cyan"))
        update_command = ["sudo", "apt-get", "update"]
        subprocess.run(update_command, check=True)

        click.echo(click.style("\n--> Installing 'wireguard' package...", fg="cyan"))
        install_command = ["sudo", "apt-get", "install", "-y", "wireguard"]
        subprocess.run(install_command, check=True)

        click.echo(click.style("\n🎉 WireGuard installed successfully!", fg="green"))
        click.echo(
            click.style(
                "   You can now use commands like 'wireguard genkey'.",
                fg="green",
            ),
        )

    except subprocess.CalledProcessError as e:
        click.echo(
            click.style(f"\n❌ An error occurred during installation: {e}", fg="red"),
            err=True,
        )
        click.echo(
            click.style(
                "   Please try running the installation manually: 'sudo apt-get install -y wireguard'",
                fg="red",
            ),
            err=True,
        )
    except FileNotFoundError:
        click.echo(
            click.style(
                "\n❌ Command 'sudo' or 'apt-get' not found. This command only works on Debian-based systems (like Ubuntu) with sudo.",
                fg="red",
            ),
            err=True,
        )


@cli.command(name="genkey", help="Generate a new WireGuard key pair.")
def genkey() -> None:
    """Generates and displays a new WireGuard private and public key pair."""
    try:
        private_key_process = subprocess.run(
            ["wg", "genkey"],
            capture_output=True,
            text=True,
            check=True,
        )
        private_key = private_key_process.stdout.strip()
        public_key_process = subprocess.run(
            ["wg", "pubkey"],
            input=private_key,
            capture_output=True,
            text=True,
            check=True,
        )
        public_key = public_key_process.stdout.strip()

        click.echo(click.style("🔑 New key pair generated successfully!\n", fg="green"))
        click.echo(f"{click.style('PrivateKey:', fg='cyan')} {private_key}")
        click.echo(f"{click.style('PublicKey: ', fg='green')} {public_key}")
    except FileNotFoundError:
        click.echo(
            click.style(
                "\n❌ Command failed. Please ensure WireGuard tools (`wg`) are installed.",
                fg="red",
            ),
            err=True,
        )
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"\n❌ Error generating keys: {e}", fg="red"), err=True)


if __name__ == "__main__":
    cli()
