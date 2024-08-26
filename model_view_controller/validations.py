import logging
from typing import Dict

from schema import Schema, And, SchemaError

CONFIG_FILE_SCHEMA: Schema = Schema(
    {
        "context": And(
            dict, error="Config.yaml `context` is required and must be a Dict."
        ),
        "connection": And(
            dict, error="Config.yaml `connection` is required and must be a Dict."
        ),
        "schemas": And(
            list, error="Config.yaml `schemas` is required and must be a List."
        ),
    }
)

TABLE_FILE_SCHEMA: Schema = Schema(
    {
        "name": And(str, error="Table.yaml `name` is required and must be a string."),
        "description": And(
            str, error="Table.yaml `description` is required and must be a string."
        ),
        "schema": And(
            str, error="Table.yaml `schema` is required and must be a string."
        ),
        "columns": And(
            list, error="Table.yaml `columns` is required and must be a List."
        ),
    }
)


def validate_config_file(config_file: dict) -> None:
    """
    Validates the config file and logs any validation errors.

    Args:
        config_file: The config file as a dictionary.
    """
    logging.info("Validating config file.")
    try:
        CONFIG_FILE_SCHEMA.validate(config_file)
        logging.info("Config file validation successful.")
    except SchemaError as e:
        logging.error(f"Config file validation failed: {str(e)}")
        for error in e.errors:
            logging.error(f"- {error}")
        raise ValueError(
            "Config file validation failed. Please check the logs for details."
        )


def validate_table_file(table_file: Dict) -> None:
    """
    Validates the table file and logs any validation errors.

    Args:
        table_file: The table file as a dictionary.
    """
    logging.info(f"Validating table file: {table_file}.")
    try:
        TABLE_FILE_SCHEMA.validate(table_file)
        logging.info("Table file validation successful.")
    except SchemaError as e:
        logging.error(f"Table file validation failed: {str(e)}")
        for error in e.errors:
            logging.error(f"- {error}")
        raise ValueError(
            f"Table {table_file} file validation failed. Please check the logs for details."
        )
