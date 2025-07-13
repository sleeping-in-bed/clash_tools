#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash Docker Proxy Management Script
Support one-click enable and disable Docker proxy settings for Clash
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import click

# Global default proxy settings
DEFAULT_PROXY = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
    'no_proxy': 'localhost,127.0.0.1,::1'
}


class DockerProxyManager:
    def __init__(self):
        # Docker config file paths
        self.docker_config_dir = Path.home() / '.docker'
        self.docker_config_file = self.docker_config_dir / 'config.json'

        # systemd service config paths
        self.systemd_dir = Path('/etc/systemd/system/docker.service.d')
        self.systemd_proxy_file = self.systemd_dir / 'http-proxy.conf'

        # Use global proxy settings
        self.proxy_settings = DEFAULT_PROXY.copy()

    def check_root(self):
        """Check if running with root privileges"""
        return os.geteuid() == 0

    def restart_docker(self):
        """Restart Docker service"""
        try:
            click.echo("Restarting Docker service...")
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'restart', 'docker'], check=True)
            click.echo(click.style("✅ Docker service restarted successfully", fg='green'))
            return True
        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"❌ Failed to restart Docker service: {e}", fg='red'))
            return False

    def enable_docker_client_proxy(self):
        """Enable Docker client proxy"""
        try:
            # Create config directory
            self.docker_config_dir.mkdir(exist_ok=True)

            # Read existing config
            config = {}
            if self.docker_config_file.exists():
                with open(self.docker_config_file, 'r') as f:
                    config = json.load(f)

            # Add proxy configuration
            config['proxies'] = {
                'default': {
                    'httpProxy': self.proxy_settings['http'],
                    'httpsProxy': self.proxy_settings['https'],
                    'noProxy': self.proxy_settings['no_proxy']
                }
            }

            # Write config file
            with open(self.docker_config_file, 'w') as f:
                json.dump(config, f, indent=2)

            click.echo(click.style("✅ Docker client proxy enabled", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"❌ Failed to enable Docker client proxy: {e}", fg='red'))
            return False

    def disable_docker_client_proxy(self):
        """Disable Docker client proxy"""
        try:
            if not self.docker_config_file.exists():
                click.echo(click.style("✅ Docker client proxy config file not found, no need to disable", fg='green'))
                return True

            # Read existing config
            with open(self.docker_config_file, 'r') as f:
                config = json.load(f)

            # Remove proxy configuration
            if 'proxies' in config:
                del config['proxies']

            # Write config file
            with open(self.docker_config_file, 'w') as f:
                json.dump(config, f, indent=2)

            click.echo(click.style("✅ Docker client proxy disabled", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"❌ Failed to disable Docker client proxy: {e}", fg='red'))
            return False

    def enable_docker_daemon_proxy(self):
        """Enable Docker daemon proxy"""
        try:
            # Create systemd config directory
            self.systemd_dir.mkdir(parents=True, exist_ok=True)

            # Create proxy config file
            proxy_config = f"""[Service]
Environment="HTTP_PROXY={self.proxy_settings['http']}"
Environment="HTTPS_PROXY={self.proxy_settings['https']}"
Environment="NO_PROXY={self.proxy_settings['no_proxy']}"
"""

            with open(self.systemd_proxy_file, 'w') as f:
                f.write(proxy_config)

            click.echo(click.style("✅ Docker daemon proxy enabled", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"❌ Failed to enable Docker daemon proxy: {e}", fg='red'))
            return False

    def disable_docker_daemon_proxy(self):
        """Disable Docker daemon proxy"""
        try:
            if self.systemd_proxy_file.exists():
                self.systemd_proxy_file.unlink()
                click.echo(click.style("✅ Docker daemon proxy disabled", fg='green'))
            else:
                click.echo(click.style("✅ Docker daemon proxy config file not found, no need to disable", fg='green'))
            return True
        except Exception as e:
            click.echo(click.style(f"❌ Failed to disable Docker daemon proxy: {e}", fg='red'))
            return False

    def check_proxy_status(self):
        """Check proxy status"""
        click.echo(click.style("=== Docker Proxy Status ===", fg='blue', bold=True))

        # Check client proxy
        if self.docker_config_file.exists():
            try:
                with open(self.docker_config_file, 'r') as f:
                    config = json.load(f)
                if 'proxies' in config:
                    click.echo(click.style("🟢 Docker client proxy: Enabled", fg='green'))
                    proxy_info = config['proxies']['default']
                    click.echo(f"   HTTP Proxy: {proxy_info.get('httpProxy', 'N/A')}")
                    click.echo(f"   HTTPS Proxy: {proxy_info.get('httpsProxy', 'N/A')}")
                    click.echo(f"   No Proxy: {proxy_info.get('noProxy', 'N/A')}")
                else:
                    click.echo(click.style("🔴 Docker client proxy: Disabled", fg='red'))
            except:
                click.echo(click.style("🔴 Docker client proxy: Config file read failed", fg='red'))
        else:
            click.echo(click.style("🔴 Docker client proxy: Disabled", fg='red'))

        # Check daemon proxy
        if self.systemd_proxy_file.exists():
            click.echo(click.style("🟢 Docker daemon proxy: Enabled", fg='green'))
            try:
                with open(self.systemd_proxy_file, 'r') as f:
                    content = f.read()
                    click.echo("   Configuration:")
                    for line in content.strip().split('\n'):
                        if line.startswith('Environment='):
                            click.echo(f"   {line}")
            except:
                click.echo(click.style("   Config file read failed", fg='red'))
        else:
            click.echo(click.style("🔴 Docker daemon proxy: Disabled", fg='red'))

    def enable_proxy(self, proxy_url=None):
        """Enable proxy"""
        if proxy_url:
            self.proxy_settings['http'] = proxy_url
            self.proxy_settings['https'] = proxy_url

        click.echo(click.style("=== Enabling Docker Proxy ===", fg='blue', bold=True))

        # Enable client proxy
        client_success = self.enable_docker_client_proxy()

        # Enable daemon proxy (requires root privileges)
        daemon_success = True
        if self.check_root():
            daemon_success = self.enable_docker_daemon_proxy()
            if daemon_success:
                self.restart_docker()
        else:
            click.echo(click.style("⚠️  Root privileges required for Docker daemon proxy", fg='yellow'))
            click.echo("   Please run with sudo or configure daemon proxy manually")

        if client_success:
            click.echo(click.style("🎉 Docker proxy enabled successfully!", fg='green', bold=True))
        else:
            click.echo(click.style("❌ Failed to enable Docker proxy", fg='red', bold=True))

    def disable_proxy(self):
        """Disable proxy"""
        click.echo(click.style("=== Disabling Docker Proxy ===", fg='blue', bold=True))

        # Disable client proxy
        client_success = self.disable_docker_client_proxy()

        # Disable daemon proxy (requires root privileges)
        daemon_success = True
        if self.check_root():
            daemon_success = self.disable_docker_daemon_proxy()
            if daemon_success:
                self.restart_docker()
        else:
            click.echo(click.style("⚠️  Root privileges required for Docker daemon proxy", fg='yellow'))
            click.echo("   Please run with sudo or configure daemon proxy manually")

        if client_success:
            click.echo(click.style("🎉 Docker proxy disabled successfully!", fg='green', bold=True))
        else:
            click.echo(click.style("❌ Failed to disable Docker proxy", fg='red', bold=True))


# Create Click command group
@click.group()
@click.version_option(version='1.0.0', prog_name='Clash Docker Proxy Manager')
@click.pass_context
def cli(ctx):
    """Clash Docker Proxy Management Tool

    Support one-click enable and disable Docker proxy settings for Clash,
    including client proxy and daemon proxy.
    """
    # Initialize context object
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj['manager'] = DockerProxyManager()


@cli.command()
@click.option('--proxy', '-p',
              default=DEFAULT_PROXY['http'],
              help=f'Proxy URL (default: {DEFAULT_PROXY["http"]})',
              show_default=True)
@click.pass_context
def enable(ctx, proxy):
    """Enable Docker proxy

    \b
    Examples:
        ./clash_docker enable
        ./clash_docker enable --proxy http://192.168.1.100:8080
        ./clash_docker enable -p socks5://127.0.0.1:1080
    """
    manager = ctx.obj['manager']
    manager.enable_proxy(proxy)


@cli.command()
@click.pass_context
def disable(ctx):
    """Disable Docker proxy

    \b
    Examples:
        ./clash_docker disable
    """
    manager = ctx.obj['manager']
    manager.disable_proxy()


@cli.command()
@click.pass_context
def status(ctx):
    """Check Docker proxy status

    \b
    Examples:
        ./clash_docker status
    """
    manager = ctx.obj['manager']
    manager.check_proxy_status()


@cli.command()
@click.pass_context
def reset(ctx):
    """Reset all Docker proxy configurations

    This will completely remove all Docker proxy settings including:
    - Docker client proxy configuration
    - Docker daemon proxy configuration

    \b
    Examples:
        ./clash_docker reset
    """
    manager = ctx.obj['manager']

    click.echo(click.style("=== Resetting Docker Proxy Configurations ===", fg='blue', bold=True))
    click.echo("This will remove:")
    click.echo("- Docker client proxy configuration")
    click.echo("- Docker daemon proxy configuration")

    manager.disable_proxy()
    click.echo(click.style("✅ All configurations have been reset", fg='green'))


if __name__ == '__main__':
    cli()
