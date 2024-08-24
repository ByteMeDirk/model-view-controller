import logging

import click
from sqlalchemy import create_engine, inspect, text, MetaData

from model_view_controller.controller import process_model
from .config import read_yaml_file, get_model_configs, get_config
from .model import create_model_from_yaml

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    """Main CLI group."""
    pass


@cli.command()
@click.argument("path")
@click.option("--path", "-p")
@click.option("--force", is_flag=True, help="Force update even if table has data", default=False)
def build(path, force):
    """Build database schema based on model configurations."""
    try:
        config = get_config(path=path)
        connection_string, schema = (
            config["database"]["connection"],
            config["database"]["schema"],
        )
        models_paths = get_model_configs(path=path)
        engine = create_engine(connection_string)
        inspector = inspect(engine)

        with engine.begin() as connection:
            # Process existing models
            for model_path in models_paths:
                process_model(connection, inspector, schema, model_path, force)

            # Check for tables to drop
            existing_tables = set(inspector.get_table_names(schema=schema))
            model_tables = set(model_path.split("/")[-1].split(".")[0] for model_path in models_paths)
            tables_to_drop = existing_tables - model_tables

            for table_name in tables_to_drop:
                if force:
                    connection.execute(text(f"DROP TABLE IF EXISTS {schema}.{table_name}"))
                    logging.info(f"Dropped table {table_name}")
                else:
                    logging.warning(f"Table {table_name} exists in database but not in configs. Use --force to drop.")

        # Force a new connection to see changes
        with engine.connect() as connection:
            for model_path in models_paths:
                table_name = model_path.split("/")[-1].split(".")[0]
                result = connection.execute(
                    text(f"SELECT * FROM {schema}.{table_name} LIMIT 0")
                )
                logging.info("Table structure after changes: %s", result.keys())

    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        raise

@cli.command()
@click.argument("path")
@click.option("--path", "-p")
@click.option("--force", is_flag=True, help="Force drop without confirmation")
def drop(path, force):
    """Drop all tables from the database schema."""
    try:
        config = get_config(path=path)
        connection_string, schema = (
            config["database"]["connection"],
            config["database"]["schema"],
        )
        engine = create_engine(connection_string)
        metadata = MetaData(schema=schema)
        metadata.reflect(bind=engine)

        if not force:
            confirmation = input("Are you sure you want to drop all tables? Type 'yes' to confirm: ")
            if confirmation.lower() != 'yes':
                logging.info("Operation cancelled.")
                return

        metadata.drop_all(bind=engine)
        logging.info("Successfully dropped all tables from schema: %s", schema)
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        raise


if __name__ == "__main__":
    cli()
