"""Team management CLI commands."""

import httpx
import typer
from rich.console import Console
from rich.table import Table

from cli.config_cmd import load_config

team_app = typer.Typer(help="Manage team members.")
console = Console()


def _client(config: dict) -> httpx.Client:
    token = config.get("token")
    if not token:
        console.print("[red]Not logged in.[/red]")
        raise typer.Exit(1)
    return httpx.Client(
        base_url=config["api_url"],
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )


@team_app.command("list")
def list_members():
    """List team members."""
    config = load_config()
    client = _client(config)
    res = client.get("/api/v1/tenant/members")
    if res.status_code != 200:
        console.print("[red]Failed to fetch members.[/red]")
        return
    members = res.json()

    table = Table(title="Team Members")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Role")
    table.add_column("Access Tier")

    for m in members:
        table.add_row(
            m.get("display_name", ""),
            m.get("email", ""),
            m.get("role", ""),
            str(m.get("access_tier", 1)),
        )
    console.print(table)


@team_app.command("invite")
def invite_member(
    email: str = typer.Argument(..., help="Email address to invite"),
    role: str = typer.Option("member", "--role", "-r", help="Role: owner|admin|member|viewer"),
    tier: int = typer.Option(1, "--tier", "-t", help="Access tier (1-10)"),
):
    """Invite a new team member."""
    config = load_config()
    client = _client(config)
    res = client.post(
        "/api/v1/tenant/members/invite",
        json={"email": email, "role": role, "access_tier": tier},
    )
    if res.status_code == 201:
        console.print(f"[green]✓[/green] Invited {email} as {role} (tier {tier})")
    else:
        console.print(f"[red]Failed: {res.json().get('detail', 'Error')}[/red]")
