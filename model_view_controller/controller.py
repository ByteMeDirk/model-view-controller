import logging
from typing import Dict, Any

from sqlalchemy import text, inspect
from sqlalchemy.engine import Connection
from sqlalchemy.orm import DeclarativeBase

from .config import read_yaml_file
from .model import create_model_from_yaml

logging.basicConfig(level=logging.INFO)


class Controller:
    @staticmethod
    def build(connection: Connection, model: DeclarativeBase) -> None:
        """
        Create database tables based on the model.

        Args:
            connection (Connection): SQLAlchemy database connection
            model (DeclarativeBase): SQLAlchemy model class
        """
        model.metadata.create_all(connection)

    @staticmethod
    def destroy(connection: Connection, model: DeclarativeBase) -> None:
        """
        Drop database tables based on the model.

        Args:
            connection (Connection): SQLAlchemy database connection
            model (DeclarativeBase): SQLAlchemy model class
        """
        model.metadata.drop_all(connection)


def table_schema_matches(
    inspector: inspect, schema: str, table_name: str, model_class: DeclarativeBase
) -> bool:
    """
    Check if the existing table schema matches the model class.

    Args:
        inspector (inspect): SQLAlchemy inspector
        schema (str): Database schema
        table_name (str): Name of the table
        model_class (DeclarativeBase): SQLAlchemy model class

    Returns:
        bool: True if the schema matches, False otherwise
    """
    existing_columns: Dict[str, Dict[str, Any]] = {
        col["name"]: col for col in inspector.get_columns(table_name, schema=schema)
    }
    model_columns: Dict[str, Any] = {
        col.name: col for col in model_class.__table__.columns
    }

    if len(existing_columns) != len(model_columns):
        return False

    for col_name, column in model_columns.items():
        if col_name not in existing_columns:
            return False
        if str(existing_columns[col_name]["type"]) != str(column.type):
            return False

    return True


def process_model(
    connection: Connection,
    inspector: inspect,
    schema: str,
    model_path: str,
    force: bool,
) -> None:
    """
    Process a model file and update or create the corresponding database table.

    Args:
        connection (Connection): SQLAlchemy database connection
        inspector (inspect): SQLAlchemy inspector
        schema (str): Database schema
        model_path (str): Path to the model YAML file
        force (bool): Force update even if table has data
    """
    table_name: str = model_path.split("/")[-1].split(".")[0]
    logging.info("Processing model: %s", table_name)

    model_dict: Dict[str, Any] = read_yaml_file(model_path)
    model_class: DeclarativeBase = create_model_from_yaml(
        table_name=table_name, schema=schema, yaml_config=model_dict
    )

    if inspector.has_table(table_name, schema=schema):
        if table_schema_matches(inspector, schema, table_name, model_class):
            logging.info(
                f"Table {table_name} schema matches exactly. No changes needed."
            )
        else:
            logging.info(f"Updating existing table: {table_name}")
            update_existing_table(
                connection, inspector, schema, table_name, model_class, force
            )
    else:
        logging.info(f"Creating new table: {table_name}")
        create_new_table(connection, model_class)


def update_existing_table(
    connection: Connection,
    inspector: inspect,
    schema: str,
    table_name: str,
    model_class: DeclarativeBase,
    force: bool,
) -> None:
    """
    Update an existing table based on the model.

    Args:
        connection (Connection): SQLAlchemy connection
        inspector (inspect): SQLAlchemy inspector
        schema (str): Database schema
        table_name (str): Name of the table
        model_class (DeclarativeBase): SQLAlchemy model class
        force (bool): Force update even if table has data
    """
    existing_columns: Dict[str, Dict[str, Any]] = {
        col["name"]: col for col in inspector.get_columns(table_name, schema=schema)
    }
    model_columns: Dict[str, Any] = {
        col.name: col for col in model_class.__table__.columns
    }

    add_new_columns(
        connection=connection,
        schema=schema,
        table_name=table_name,
        model_columns=model_columns,
        existing_columns=existing_columns,
    )

    remove_deleted_columns(
        connection=connection,
        schema=schema,
        table_name=table_name,
        model_columns=model_columns,
        existing_columns=existing_columns,
        force=force,
    )

    update_column_types(
        connection=connection,
        schema=schema,
        table_name=table_name,
        model_columns=model_columns,
        existing_columns=existing_columns,
    )

    logging.info("Updated table: %s", table_name)


def add_new_columns(
    connection: Connection,
    schema: str,
    table_name: str,
    model_columns: Dict[str, Any],
    existing_columns: Dict[str, Dict[str, Any]],
) -> None:
    """
    Add new columns to the table.

    Args:
        connection (Connection): SQLAlchemy connection
        schema (str): Database schema
        table_name (str): Name of the table
        model_columns (Dict[str, Any]): Columns from the model
        existing_columns (Dict[str, Dict[str, Any]]): Existing columns in the database
    """
    for col_name, column in model_columns.items():
        if col_name not in existing_columns:
            column_creation: str = (
                f"ALTER TABLE {schema}.{table_name} ADD COLUMN {col_name} {column.type}"
            )
            execute_sql(
                connection,
                column_creation,
                f"Added new column {col_name} to table {table_name}",
            )


def remove_deleted_columns(
    connection: Connection,
    schema: str,
    table_name: str,
    model_columns: Dict[str, Any],
    existing_columns: Dict[str, Dict[str, Any]],
    force: bool,
) -> None:
    """
    Remove deleted columns from the table.

    Args:
        connection (Connection): SQLAlchemy connection
        schema (str): Database schema
        table_name (str): Name of the table
        model_columns (Dict[str, Any]): Columns from the model
        existing_columns (Dict[str, Dict[str, Any]]): Existing columns in the database
        force (bool): Force column deletion even if it contains data
    """
    for col_name in existing_columns:
        if col_name not in model_columns:
            if has_data(connection, schema, table_name, col_name):
                if force:
                    column_deletion: str = (
                        f"ALTER TABLE {schema}.{table_name} DROP COLUMN {col_name}"
                    )
                    execute_sql(
                        connection,
                        column_deletion,
                        f"Deleted column {col_name} from table {table_name}",
                    )
                else:
                    logging.warning(
                        f"Column {col_name} in table {table_name} contains data. Use --force to drop."
                    )
            else:
                column_deletion: str = (
                    f"ALTER TABLE {schema}.{table_name} DROP COLUMN {col_name}"
                )
                execute_sql(
                    connection,
                    column_deletion,
                    f"Deleted column {col_name} from table {table_name}",
                )


def has_data(
    connection: Connection, schema: str, table_name: str, column_name: str
) -> bool:
    """
    Check if a column has any non-null data.

    Args:
        connection (Connection): SQLAlchemy connection
        schema (str): Database schema
        table_name (str): Name of the table
        column_name (str): Name of the column

    Returns:
        bool: True if the column has data, False otherwise
    """
    query: text = text(
        f"SELECT COUNT(*) FROM {schema}.{table_name} WHERE {column_name} IS NOT NULL"
    )
    result: int = connection.execute(query).scalar()
    return result > 0


def update_column_types(
    connection: Connection,
    schema: str,
    table_name: str,
    model_columns: Dict[str, Any],
    existing_columns: Dict[str, Dict[str, Any]],
) -> None:
    """
    Update column types if needed.

    Args:
        connection (Connection): SQLAlchemy connection
        schema (str): Database schema
        table_name (str): Name of the table
        model_columns (Dict[str, Any]): Columns from the model
        existing_columns (Dict[str, Dict[str, Any]]): Existing columns in the database
    """
    for col_name, column in model_columns.items():
        if col_name in existing_columns:
            existing_type: str = existing_columns[col_name]["type"]
            if str(existing_type) != str(column.type):
                alter_column: str = (
                    f"ALTER TABLE {schema}.{table_name} ALTER COLUMN {col_name} TYPE {column.type}"
                )
                execute_sql(
                    connection,
                    alter_column,
                    f"Altered column {col_name} in table {table_name}",
                )


def create_new_table(connection: Connection, model_class: DeclarativeBase) -> None:
    """
    Create a new table based on the model.

    Args:
        connection (Connection): SQLAlchemy connection
        model_class (DeclarativeBase): SQLAlchemy model class
    """
    model_class.__table__.create(connection)
    logging.info("Created new table: %s", model_class.__tablename__)


def execute_sql(connection: Connection, sql: str, success_message: str) -> None:
    """
    Execute SQL statement and log the result.

    Args:
        connection (Connection): SQLAlchemy connection
        sql (str): SQL statement to execute
        success_message (str): Message to log on successful execution
    """
    try:
        connection.execute(text(sql))
        connection.execute(text("COMMIT"))
        logging.info(success_message)
    except Exception as e:
        logging.error("Error executing SQL: %s", str(e))
