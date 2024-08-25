import logging

import click

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    """Main CLI group for model_view_controller operations."""
    pass


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
