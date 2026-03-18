"""CLI config management — stores settings in ~/.cereborate/config.json"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

config_app = typer.Typer(help="Manage Cereborate CLI configuration.")
console = Console()

CONFIG_PATH = Path.home() / ".cereborate" / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"api_url": "http://localhost:8000", "token": None}
    return json.loads(CONFIG_PATH.read_text())


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


@config_app.command("set-url")
def set_url(url: str = typer.Argument(..., help="Backend API URL")):
    """Set the backend API URL."""
    config = load_config()
    config["api_url"] = url
    save_config(config)
    console.print(f"[green]✓[/green] API URL set to: {url}")


@config_app.command("set-model")
def set_model(
    task: str = typer.Argument(..., help="Task: planning|classifier|embedding"),
    model: str = typer.Argument(..., help="Model name"),
):
    """Set the LLM model for a specific task."""
    config = load_config()
    config[f"model_{task}"] = model
    save_config(config)
    console.print(f"[green]✓[/green] {task} model set to: {model}")


@config_app.command("show")
def show_config():
    """Show current configuration."""
    config = load_config()
    table = Table(title="Cereborate Config")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    for key, value in config.items():
        display_value = "***" if key == "token" and value else str(value or "not set")
        table.add_row(key, display_value)
    console.print(table)
