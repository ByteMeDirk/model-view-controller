import logging

from sqlalchemy import text

from .config import read_yaml_file
from .model import create_model_from_yaml

logging.basicConfig(level=logging.INFO)


class Controller:

    @staticmethod
    def build(connection, model):
        """
        Create database tables based on the model.

        Args:
            connection: SQLAlchemy database connection
            model: SQLAlchemy model class
        """
        model.metadata.create_all(connection)

    @staticmethod
    def destroy(connection, model):
        """
        Drop database tables based on the model.

        Args:
            connection: SQLAlchemy database connection
            model: SQLAlchemy model class
        """
        model.metadata.drop_all(connection)


def table_schema_matches(inspector, schema, table_name, model_class):
    existing_columns = {
        col["name"]: col for col in inspector.get_columns(table_name, schema=schema)
    }
    model_columns = {col.name: col for col in model_class.__table__.columns}

    if len(existing_columns) != len(model_columns):
        return False

    for col_name, column in model_columns.items():
        if col_name not in existing_columns:
            return False
        if str(existing_columns[col_name]["type"]) != str(column.type):
            return False

    return True


def process_model(connection, inspector, schema, model_path, force):
    table_name = model_path.split("/")[-1].split(".")[0]
    logging.info("Processing model: %s", table_name)
    model_dict = read_yaml_file(model_path)
    model_class = create_model_from_yaml(
        table_name=table_name,
        schema=schema,
        yaml_config=model_dict
    )

    if inspector.has_table(table_name, schema=schema):
        if table_schema_matches(inspector, schema, table_name, model_class):
            logging.info(f"Table {table_name} schema matches exactly. No changes needed.")
        else:
            logging.info(f"Updating existing table: {table_name}")
            update_existing_table(connection, inspector, schema, table_name, model_class, force)
    else:
        logging.info(f"Creating new table: {table_name}")
        create_new_table(connection, model_class)


def update_existing_table(connection, inspector, schema, table_name, model_class, force):
    """
    Update an existing table based on the model.

    Args:
        connection: SQLAlchemy connection
        inspector: SQLAlchemy inspector
        schema (str): Database schema
        table_name (str): Name of the table
        model_class: SQLAlchemy model class
        force (bool): Force update even if table has data
    """
    existing_columns = {
        col["name"]: col for col in inspector.get_columns(table_name, schema=schema)
    }
    model_columns = {col.name: col for col in model_class.__table__.columns}

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
    )
    update_column_types(
        connection=connection,
        schema=schema,
        table_name=table_name,
        model_columns=model_columns,
        existing_columns=existing_columns,
    )

    logging.info("Updated table: %s", table_name)


def add_new_columns(connection, schema, table_name, model_columns, existing_columns):
    """Add new columns to the table."""
    for col_name, column in model_columns.items():
        if col_name not in existing_columns:
            column_creation = f"ALTER TABLE {schema}.{table_name} ADD COLUMN {col_name} {column.type}"
            execute_sql(
                connection,
                column_creation,
                f"Added new column {col_name} to table {table_name}",
            )

def remove_deleted_columns(connection, schema, table_name, model_columns, existing_columns, force):
    """Remove deleted columns from the table."""
    for col_name in existing_columns:
        if col_name not in model_columns:
            if has_data(connection, schema, table_name, col_name):
                if force:
                    column_deletion = f"ALTER TABLE {schema}.{table_name} DROP COLUMN {col_name}"
                    execute_sql(
                        connection,
                        column_deletion,
                        f"Deleted column {col_name} from table {table_name}",
                    )
                else:
                    logging.warning(f"Column {col_name} in table {table_name} contains data. Use --force to drop.")
            else:
                column_deletion = f"ALTER TABLE {schema}.{table_name} DROP COLUMN {col_name}"
                execute_sql(
                    connection,
                    column_deletion,
                    f"Deleted column {col_name} from table {table_name}",
                )


def has_data(connection, schema, table_name, column_name):
    """Check if a column has any non-null data."""
    query = text(f"SELECT COUNT(*) FROM {schema}.{table_name} WHERE {column_name} IS NOT NULL")
    result = connection.execute(query).scalar()
    return result > 0


def remove_deleted_columns(
        connection, schema, table_name, model_columns, existing_columns
):
    """Remove deleted columns from the table."""
    for col_name in existing_columns:
        if col_name not in model_columns:
            column_deletion = (
                f"ALTER TABLE {schema}.{table_name} DROP COLUMN {col_name}"
            )
            execute_sql(
                connection,
                column_deletion,
                f"Deleted column {col_name} from table {table_name}",
            )


def update_column_types(
        connection, schema, table_name, model_columns, existing_columns
):
    """Update column types if needed."""
    for col_name, column in model_columns.items():
        if col_name in existing_columns:
            existing_type = existing_columns[col_name]["type"]
            if str(existing_type) != str(column.type):
                alter_column = f"ALTER TABLE {schema}.{table_name} ALTER COLUMN {col_name} TYPE {column.type}"
                execute_sql(
                    connection,
                    alter_column,
                    f"Altered column {col_name} in table {table_name}",
                )


def create_new_table(connection, model_class):
    """Create a new table based on the model."""
    model_class.__table__.create(connection)
    logging.info("Created new table: %s", model_class.__tablename__)


def execute_sql(connection, sql, success_message):
    """Execute SQL statement and log the result."""
    try:
        connection.execute(text(sql))
        connection.execute(text("COMMIT"))
        logging.info(success_message)
    except Exception as e:
        logging.error("Error executing SQL: %s", str(e))
