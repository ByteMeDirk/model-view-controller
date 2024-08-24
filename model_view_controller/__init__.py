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
def build(path):
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
            for model_path in models_paths:
                process_model(connection, inspector, schema, model_path)

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
def drop(path):
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
        metadata.drop_all(bind=engine)
        logging.info("Successfully dropped all tables from schema: %s", schema)
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        raise


if __name__ == "__main__":
    cli()
