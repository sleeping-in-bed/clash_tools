#!/usr/bin/env python
import os
import subprocess
from pathlib import Path

import click
from jinja2 import Environment, FileSystemLoader

# Base path definitions
BASE_DIR = Path(__file__).parent.resolve()
TEMPLATE_DIR = BASE_DIR / "templates"
SERVER_SETTINGS_PATH = BASE_DIR / "server_settings.py"
CLIENT_SETTINGS_PATH = BASE_DIR / "client_settings.py"

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)


def render_template(template_name: str, context: dict, output_path: Path):
    """Renders a Jinja2 template and writes it to a file."""
    template = env.get_template(template_name)
    rendered_content = template.render(context)
    output_path.write_text(rendered_content, encoding="utf-8")
    click.echo(click.style(f"✓ File generated: {output_path}", fg="green"))


def run_compose_command(command: str, compose_file_name: str):
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
            click.style(f"\n❌ Failed to {command} service: {e}", fg="red"), err=True
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
def cli():
    """A tool to manage WireGuard server and client configurations."""
    pass


# --- Server Command Group ---
@cli.group()
def server():
    """Manage server configuration and services."""
    pass


@server.command(name="up", help="Generate server config files and start the service.")
def server_up():
    """Generates server config files and starts the service."""
    from clash_tools.wireguard.server_settings import SERVER_CONFIG

    click.echo(
        click.style("🚀 Generating server configuration files...", fg="cyan", bold=True)
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
def server_down():
    """Stops and removes the server service."""
    click.echo(click.style("🚀 Stopping server...", fg="cyan", bold=True))
    run_compose_command("down", "server_compose.yml")


# --- Client Command Group ---
@cli.group()
def client():
    """Manage client configuration and services."""
    pass


@client.command(name="up", help="Generate client config files and start the service.")
def client_up():
    """Generates client config files and starts the service."""
    from clash_tools.wireguard.client_settings import CLIENT_CONFIG

    click.echo(
        click.style("🚀 Generating client configuration files...", fg="cyan", bold=True)
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
        )
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
def client_down():
    """Stops and removes the client service."""
    click.echo(click.style("🚀 Stopping client...", fg="cyan", bold=True))
    run_compose_command("down", "client_compose.yml")


@client.command(name="check-ip", help="Check the host's public IP to verify the VPN connection.")
def check_ip():
    """Checks the host's public IP to see if it matches the VPN server."""
    click.echo(click.style("🔎 Checking host's public IP...", fg="cyan", bold=True))

    # 1. Get server IP from settings
    server_ip = None
    try:
        from clash_tools.wireguard.client_settings import CLIENT_CONFIG
        endpoint = CLIENT_CONFIG.get("PEER", {}).get("endpoint")
        if not endpoint or ":" not in endpoint:
            click.echo(
                click.style(f"❌ Invalid or missing endpoint in client_settings.py: '{endpoint}'", fg="red"),
                err=True,
            )
            return
        server_ip = endpoint.split(':')[0]
        click.echo(f"ℹ️  VPN Server IP (from settings): {click.style(server_ip, fg='blue')}")
    except ImportError:
        click.echo(click.style("❌ Could not import client_settings.py.", fg="red"), err=True)
        return
    except Exception as e:
        click.echo(click.style(f"❌ Error reading server IP from settings: {e}", fg="red"), err=True)
        return

    # 2. Get public IP from external services
    ip_services = ["ifconfig.me", "ip.sb"]
    public_ip = None
    click.echo(click.style("⏳ Querying external services to find public IP...", fg="cyan"))
    for service in ip_services:
        try:
            result = subprocess.run(
                ["curl", "-s", "-4", service],
                capture_output=True, text=True, check=True, timeout=10
            )
            fetched_ip = result.stdout.strip()
            # A simple sanity check for an IP address format
            if len(fetched_ip.split('.')) == 4:
                public_ip = fetched_ip
                click.echo(f"   ✓ Found host public IP via {service}: {click.style(public_ip, fg='blue')}")
                break
            else:
                click.echo(click.style(f"   ⚠️ Got invalid response from {service}", fg="yellow"), err=True)
        except FileNotFoundError:
            click.echo(
                click.style("❌ Command `curl` not found. Please install curl to use this feature.", fg="red"),
                err=True,
            )
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            click.echo(click.style(f"   ⚠️ Failed to get IP from {service}, trying next...", fg="yellow"))
            continue

    if not public_ip:
        click.echo(click.style("\n❌ Failed to determine public IP after trying all available services.", fg="red"), err=True)
        return

    # 3. Compare and report
    click.echo("-" * 40)
    if public_ip == server_ip:
        click.echo(click.style("✅ SUCCESS!", fg="green", bold=True))
        click.echo(click.style(f"   Your public IP ({public_ip}) matches the VPN server IP.", fg="green"))
        click.echo(click.style("   Host traffic appears to be correctly routed through the VPN.", fg="green"))
    else:
        click.echo(click.style("❌ MISMATCH!", fg="red", bold=True))
        click.echo(click.style(f"   Your public IP is {public_ip}.", fg="red"))
        click.echo(click.style(f"   The VPN server IP is {server_ip}.", fg="red"))
        click.echo(click.style("   Host traffic is NOT being routed through the VPN.", fg="red"))
    click.echo("-" * 40)


# --- Config and Utility Command Group ---
@cli.group(help="View or edit configuration files.")
def config():
    """Manages configuration files."""
    pass


def _config_handler(config_file_path: Path, edit: bool):
    """Generic handler for config commands."""
    click.echo(
        f"Config file path: {click.style(str(config_file_path.absolute()), fg='blue')}"
    )
    if not config_file_path.exists():
        click.echo(click.style("❌ Config file not found!", fg="red"), err=True)
        return
    if edit:
        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run([editor, str(config_file_path)], check=True)
        except Exception as e:
            click.echo(click.style(f"❌ Error opening editor: {e}", fg="red"), err=True)


@config.command(name="server", help="Manage the server configuration file.")
@click.option(
    "--edit", "-e", is_flag=True, help="Open the server config file in an editor."
)
def config_server(edit: bool):
    """Displays or edits the server configuration file."""
    _config_handler(SERVER_SETTINGS_PATH, edit)


@config.command(name="client", help="Manage the client configuration file.")
@click.option(
    "--edit", "-e", is_flag=True, help="Open the client config file in an editor."
)
def config_client(edit: bool):
    """Displays or edits the client configuration file."""
    _config_handler(CLIENT_SETTINGS_PATH, edit)


@cli.command(name="install-wg", help="Install WireGuard using apt (requires sudo).")
def install_wg():
    """Installs the 'wireguard' package using apt."""
    click.echo(
        click.style(
            "🚀 This command will attempt to install WireGuard using apt.", fg="cyan"
        )
    )
    click.echo(
        click.style("   You may be prompted for your sudo password.", fg="yellow")
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
                "   You can now use commands like 'wireguard genkey'.", fg="green"
            )
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
def genkey():
    """Generates and displays a new WireGuard private and public key pair."""
    try:
        private_key_process = subprocess.run(
            ["wg", "genkey"], capture_output=True, text=True, check=True
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
