import logging
from typing import Dict, Any, List

import click
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.engine import Engine

from model_view_controller.controller import process_model
from .config import read_yaml_file, get_model_configs, get_config
from .model import create_model_from_yaml

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
@click.option(
    "--drop-tables",
    is_flag=True,
    help="Drop tables that exist in database but not in configs",
    default=False,
)
def build(path: str, force: bool, drop_tables: bool) -> None:
    """
    Build database schema based on model configurations.

    Args:
        path (str): Path to the configuration directory
        force (bool): Force column deletion even if it contains data
        drop_tables (bool): Drop tables that exist in database but not in configs
    """
    try:
        config: Dict[str, Any] = get_config(path=path)
        connection_string, schema = (
            config["database"]["connection"],
            config["database"]["schema"],
        )
        models_paths: List[str] = get_model_configs(path=path)
        engine: Engine = create_engine(connection_string)
        inspector = inspect(engine)

        with engine.begin() as connection:
            # Process existing models
            for model_path in models_paths:
                process_model(connection, inspector, schema, model_path, force)

            # Check for tables to drop
            existing_tables: set = set(inspector.get_table_names(schema=schema))
            model_tables: set = set(
                model_path.split("/")[-1].split(".")[0] for model_path in models_paths
            )
            tables_to_drop: set = existing_tables - model_tables

            for table_name in tables_to_drop:
                if drop_tables:
                    connection.execute(
                        text(f"DROP TABLE IF EXISTS {schema}.{table_name}")
                    )
                    logging.info(f"Dropped table {table_name}")
                else:
                    user_input: str = input(
                        f"Table {table_name} exists in database but not in configs. Drop it? (y/n): "
                    )
                    if user_input.lower() == "y":
                        connection.execute(
                            text(f"DROP TABLE IF EXISTS {schema}.{table_name}")
                        )
                        logging.info(f"Dropped table {table_name}")
                    else:
                        logging.warning(
                            f"Table {table_name} was not dropped. Use --drop-tables to drop automatically."
                        )

        # Force a new connection to see changes
        with engine.connect() as connection:
            for model_path in models_paths:
                table_name: str = model_path.split("/")[-1].split(".")[0]
                result = connection.execute(
                    text(f"SELECT * FROM {schema}.{table_name} LIMIT 0")
                )
                logging.info("Table structure after changes: %s", result.keys())

    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        raise


@cli.command()
@click.argument("path")
@click.option("--force", is_flag=True, help="Force drop without confirmation")
def drop(path: str, force: bool) -> None:
    """
    Drop all tables from the database schema.

    Args:
        path (str): Path to the configuration directory
        force (bool): Force drop without confirmation
    """
    try:
        config: Dict[str, Any] = get_config(path=path)
        connection_string, schema = (
            config["database"]["connection"],
            config["database"]["schema"],
        )
        engine: Engine = create_engine(connection_string)
        metadata = MetaData(schema=schema)
        metadata.reflect(bind=engine)

        if not force:
            confirmation: str = input(
                "Are you sure you want to drop all tables? Type 'yes' to confirm: "
            )
            if confirmation.lower() != "yes":
                logging.info("Operation cancelled.")
                return

        metadata.drop_all(bind=engine)
        logging.info("Successfully dropped all tables from schema: %s", schema)
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        raise


if __name__ == "__main__":
    cli()
