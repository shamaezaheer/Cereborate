import typer

from cli.plan_cmd import plan_app
from cli.ideas_cmd import ideas_app
from cli.team_cmd import team_app
from cli.config_cmd import config_app

app = typer.Typer(
    name="cereborate",
    help="Cereborate — Think together. Share smart.",
    no_args_is_help=True,
)

app.add_typer(ideas_app, name="ideas")
app.add_typer(team_app, name="team")
app.add_typer(config_app, name="config")


@app.command()
def plan():
    """Start an interactive planning session."""
    from cli.plan_cmd import start_plan_repl
    start_plan_repl()


if __name__ == "__main__":
    app()
