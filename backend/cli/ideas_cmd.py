"""Ideas management CLI commands."""

import json

import httpx
import typer
from rich.console import Console
from rich.table import Table

from cli.config_cmd import load_config

ideas_app = typer.Typer(help="Manage your ideas.")
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


@ideas_app.command("list")
def list_ideas():
    """List your ideas."""
    config = load_config()
    client = _client(config)
    res = client.get("/api/v1/ideas")
    ideas = res.json()

    table = Table(title="My Ideas")
    table.add_column("Title", style="bold")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("ID", style="dim")

    for idea in ideas:
        table.add_row(
            idea["title"],
            idea["status"],
            str(idea["version"]),
            idea["id"][:8] + "...",
        )
    console.print(table)


@ideas_app.command("show")
def show_idea(idea_id: str = typer.Argument(..., help="Idea ID")):
    """Show details of an idea."""
    config = load_config()
    client = _client(config)
    res = client.get(f"/api/v1/ideas/{idea_id}")
    if res.status_code == 404:
        console.print("[red]Idea not found.[/red]")
        return
    idea = res.json()

    console.print(f"\n[bold]{idea['title']}[/bold] [{idea['status']}]")
    if idea.get("description"):
        console.print(f"\n{idea['description']}")

    if idea.get("components"):
        console.print(f"\n[bold]Components ({len(idea['components'])})[/bold]")
        for c in idea["components"]:
            console.print(f"  • {c['name']} [{c['priority']}] — {c['status']}")


@ideas_app.command("export")
def export_idea(
    idea_id: str = typer.Argument(..., help="Idea ID"),
    format: str = typer.Option("md", "--format", "-f", help="Format: json|md"),
):
    """Export an idea."""
    config = load_config()
    client = _client(config)
    res = client.get(f"/api/v1/ideas/{idea_id}")
    if res.status_code == 404:
        console.print("[red]Idea not found.[/red]")
        return
    idea = res.json()

    if format == "json":
        console.print(json.dumps(idea, indent=2))
    else:
        # Markdown export
        md = f"# {idea['title']}\n\n"
        if idea.get("description"):
            md += f"{idea['description']}\n\n"
        md += f"**Status:** {idea['status']}  \n"
        md += f"**Version:** {idea['version']}\n\n"
        if idea.get("components"):
            md += "## Components\n\n"
            for c in idea["components"]:
                md += f"### {c['name']}\n"
                md += f"- **Priority:** {c['priority']}\n"
                md += f"- **Status:** {c['status']}\n"
                if c.get("description"):
                    md += f"\n{c['description']}\n"
                md += "\n"
        console.print(md)
