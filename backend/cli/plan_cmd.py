"""Interactive planning REPL — streams conversation with the LLM via backend API."""

import httpx
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from cli.config_cmd import load_config

plan_app = typer.Typer()
console = Console()


def _get_client(config: dict) -> tuple[httpx.Client, dict]:
    token = config.get("token")
    if not token:
        console.print("[red]Not logged in. Run: cereborate auth login[/red]")
        raise typer.Exit(1)
    headers = {"Authorization": f"Bearer {token}"}
    client = httpx.Client(base_url=config["api_url"], headers=headers, timeout=60.0)
    return client, headers


def start_plan_repl():
    """Start an interactive planning session in the terminal."""
    config = load_config()

    console.print(Panel.fit(
        "[bold cyan]Cereborate Planning[/bold cyan]\n"
        "Describe your idea and I'll help you structure it.\n"
        "[dim]Type 'done' when ready to create the idea. Ctrl+C to cancel.[/dim]",
        border_style="cyan",
    ))

    initial = Prompt.ask("\n[bold]What's your idea?[/bold]")
    if not initial.strip():
        console.print("[yellow]Cancelled.[/yellow]")
        return

    try:
        client, _ = _get_client(config)
    except typer.Exit:
        return

    # Start session
    with console.status("Starting session..."):
        res = client.post("/api/v1/plan/start", json={"message": initial})
        if res.status_code != 201:
            console.print(f"[red]Error: {res.json().get('detail', 'Failed')}[/red]")
            return
        session = res.json()

    session_id = session["id"]

    # Print initial assistant response
    history = session["conversation_history"]
    if history and history[-1]["role"] == "assistant":
        console.print(f"\n[cyan]Cereborate:[/cyan] {history[-1]['content']}\n")

    # REPL loop
    while True:
        try:
            user_input = Prompt.ask("[bold]You[/bold]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session cancelled.[/yellow]")
            return

        if user_input.lower() in ("done", "create", "finish"):
            break

        with console.status("Thinking..."):
            res = client.post(
                f"/api/v1/plan/{session_id}/respond",
                json={"message": user_input},
            )
            if res.status_code != 200:
                console.print(f"[red]Error: {res.json().get('detail', 'Failed')}[/red]")
                continue
            updated = res.json()

        history = updated["conversation_history"]
        if history and history[-1]["role"] == "assistant":
            console.print(f"\n[cyan]Cereborate:[/cyan] {history[-1]['content']}\n")

        if updated["extracted_data"].get("is_complete"):
            console.print("[green]✓ Ready to create idea. Type 'done' or keep refining.[/green]")

    # Show summary
    extracted = session.get("extracted_data", {})
    console.print("\n[bold]Idea Summary[/bold]")
    if extracted.get("title"):
        console.print(f"  Title: {extracted['title']}")
    if extracted.get("description"):
        console.print(f"  Description: {extracted['description']}")
    if extracted.get("components"):
        console.print(f"  Components: {len(extracted['components'])}")

    confirm = Prompt.ask("Create this idea?", choices=["y", "n"], default="y")
    if confirm != "y":
        console.print("[yellow]Idea not created.[/yellow]")
        return

    with console.status("Creating idea..."):
        res = client.post(f"/api/v1/plan/{session_id}/complete")
        if res.status_code != 200:
            console.print(f"[red]Error: {res.json().get('detail', 'Failed')}[/red]")
            return
        result = res.json()

    idea = result["idea"]
    console.print(
        Panel.fit(
            f"[bold green]✓ Idea created![/bold green]\n\n"
            f"[bold]{idea['title']}[/bold]\n"
            f"ID: {idea['id']}\n"
            f"Status: {idea['status']}",
            border_style="green",
        )
    )
