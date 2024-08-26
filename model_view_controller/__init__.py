import logging

import click

from model_view_controller.config import generate_workspace_state_file

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    """Main CLI group for model_view_controller operations."""
    pass


@cli.command()
@click.argument("path")
def plan(path: str) -> None:
    """
    Generate the workspace state file.

    Args:
        path (str): The path to the workspace.

    Returns:
        str: The path to the generated workspace state file.
    """
    generate_workspace_state_file(workspace_path=path)


@cli.command()
@click.argument("path")
@click.option(
    "--force",
    is_flag=True,
    help="Force column deletion even if it contains data",
    default=False,
)
def build(path: str, force: bool) -> None:
    pass


@cli.command()
@click.argument("path")
@click.option("--force", is_flag=True, help="Force drop without confirmation")
def drop(path: str, force: bool) -> None:
    pass


if __name__ == "__main__":
    cli()
