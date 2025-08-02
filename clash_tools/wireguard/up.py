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
    click.echo(f"✓ File generated: {output_path}")


def run_compose_command(command: str, compose_file_name: str):
    """Runs a docker-compose command using a specific compose file."""
    compose_file_path = BASE_DIR / compose_file_name
    if not compose_file_path.exists():
        click.echo(f"❌ Compose file not found: {compose_file_path}", err=True)
        return

    base_command = ["docker", "compose", "-f", str(compose_file_path)]
    full_command = base_command + (["up", "-d"] if command == "up" else [command])

    try:
        subprocess.run(full_command, check=True, cwd=BASE_DIR)
        status = "started" if command == "up" else "stopped"
        click.echo(f"\n🎉 Service {status} successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"\n❌ Failed to {command} service: {e}", err=True)
    except FileNotFoundError:
        click.echo(
            "\n❌ Command failed. Please ensure Docker and Docker Compose are installed.",
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
    click.echo("🚀 Generating server configuration files...")
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

    click.echo("\n🚀 Starting server...")
    run_compose_command("up", "server_compose.yml")


@server.command(name="down", help="Stop and remove the server service.")
def server_down():
    """Stops and removes the server service."""
    click.echo("🚀 Stopping server...")
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

    click.echo("🚀 Generating client configuration files...")
    render_template(
        "client_wg0.conf.j2",
        {
            "interface": CLIENT_CONFIG["INTERFACE"],
            "peer": CLIENT_CONFIG["PEER"],
        },
        BASE_DIR / "client_wg0.conf",
    )
    render_template("client_compose.yml.j2", {}, BASE_DIR / "client_compose.yml")

    click.echo("\n🚀 Starting client...")
    run_compose_command("up", "client_compose.yml")


@client.command(name="down", help="Stop and remove the client service.")
def client_down():
    """Stops and removes the client service."""
    click.echo("🚀 Stopping client...")
    run_compose_command("down", "client_compose.yml")


# --- Config and Utility Command Group ---
@cli.group(help="View or edit configuration files.")
def config():
    """Manages configuration files."""
    pass


def _config_handler(config_file_path: Path, edit: bool):
    """Generic handler for config commands."""
    click.echo(f"Config file path: {config_file_path.absolute()}")
    if not config_file_path.exists():
        click.echo("❌ Config file not found!", err=True)
        return
    if edit:
        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run([editor, str(config_file_path)], check=True)
        except Exception as e:
            click.echo(f"❌ Error opening editor: {e}", err=True)


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

        click.echo("🔑 New key pair generated successfully!\n")
        click.echo(f"{click.style('PrivateKey:', fg='cyan')} {private_key}")
        click.echo(f"{click.style('PublicKey: ', fg='green')} {public_key}")
    except FileNotFoundError:
        click.echo(
            "\n❌ Command failed. Please ensure WireGuard tools (`wg`) are installed.",
            err=True,
        )
    except subprocess.CalledProcessError as e:
        click.echo(f"\n❌ Error generating keys: {e}", err=True)


if __name__ == "__main__":
    cli()
