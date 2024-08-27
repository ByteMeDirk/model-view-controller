import logging
from typing import Dict, Any

import yaml
from sqlalchemy import create_engine, Engine, Table, MetaData, Column, inspect, text, Connection
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

from .config import read_file, find_latest_workspace_state_version, crawl_workspace

DB_TYPES: Dict = {
    "sqlite": "sqlite:///{database}",
    "mysql": "mysql://{username}:{password}@{host}:{port}/{database}",
    "postgresql": "postgresql://{username}:{password}@{host}:{port}/{database}",
    "mssql": "mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver={driver}",
    "oracle": "oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={service_name}"
}

DATA_TYPES: Dict = {
    name.lower(): getattr(types, name)
    for name in dir(types)
    if isinstance(getattr(types, name), type)
       and issubclass(getattr(types, name), types.TypeEngine)
}

Base = declarative_base()


class Model(Base):
    """Base class for all models."""

    __abstract__ = True
    __tablename__ = None
    __schema__ = None

    def get_attributes(self):
        """Get model attributes."""
        return [
            attr
            for attr in dir(self)
            if not attr.startswith("_") and not callable(getattr(self, attr))
        ]


class ModelManager:
    def __init__(self, workspace_path: str):
        self.config: Dict = yaml.safe_load(read_file(
            file_path=crawl_workspace(workspace_path)[0]
        ))
        self.workstate: Dict = yaml.safe_load(read_file(
            file_path=f"mvc_workspace_state_{find_latest_workspace_state_version() - 1}.yaml"
        ))

    def get_connection(self, db_type: str, **kwargs) -> Engine:
        """
        Get the SQLAlchemy engine.

        Args:
            db_type (str): The type of database.
            **kwargs: The connection parameters.

        Returns:
            Engine: The SQLAlchemy engine.

        Raises:
            ValueError: If the database type is invalid.
            KeyError: If the connection parameters are invalid.
        """
        if db_type not in DB_TYPES:
            logging.error(f"Invalid database type: {db_type}")
            raise ValueError(f"Invalid database type: {db_type}")

        try:
            connection_url = DB_TYPES[db_type].format(**kwargs)
            engine = create_engine(connection_url)
        except KeyError as error:
            logging.error(
                f"Expecting connection parameters: {error}, expected connection url: {DB_TYPES[db_type]} for {db_type}.")
            raise KeyError(
                f"Expecting connection parameters: {error}, expected connection url: {DB_TYPES[db_type]} for {db_type}.") from error

        self.test_connection(engine=engine, db_type=db_type)
        return engine

    @staticmethod
    def test_connection(engine: Engine, db_type: str):
        """
        Test the connection to the database.

        Args:
            engine (Engine): The SQLAlchemy engine.
            db_type (str): The type of database.

        Raises:
            Exception: If the connection fails.
        """
        try:
            engine.connect()
            logging.info(f"Connection to {db_type} successful.")
        except Exception as error:
            logging.error(f"Connection failed: {error}")
            raise error

    def get_data_type(self, config_type: str, length: [int, None] = None) -> types.TypeEngine:
        """
        Get the SQLAlchemy data type.

        Args:
            config_type (str): The data type.
            length (int, None): The length of the data type. Defaults to None.

        Returns:
            types.TypeEngine: The SQLAlchemy data type.

        Raises:
            ValueError: If the data type is invalid.
        """
        config_type = config_type.lower()
        if config_type not in DATA_TYPES:
            logging.error(f"Invalid data type: {config_type}")
            raise ValueError(f"Invalid data type: {config_type}")

        if length:
            return DATA_TYPES[config_type](length=length)
        return DATA_TYPES[config_type]

    def generate_table_object(self):
        for full_table_name, table_config in self.workstate.items():
            db_name, schema_name, table_name = full_table_name.split(".")
            columns = table_config.get("columns")
            metadata = MetaData(schema=schema_name)
            table_columns = []
            for column in columns:
                column_type = self.get_data_type(column.get("type"), column.get("length"))
                column_args = {
                    "name": column.get("name"),
                    "type_": column_type,
                    "primary_key": column.get("primary_key", False),
                    "autoincrement": column.get("auto_increment", False),
                    "nullable": column.get("nullable", False),
                    "unique": column.get("unique", False),
                }
                table_columns.append(Column(**column_args))

            table = Table(
                table_name, metadata, *table_columns, comment=table_config.get("comment", "")
            )
            class_attrs = {
                "__table__": table,
                "__tablename__": table_name,
                "__schema__": schema_name,
            }
            yield type(table_name, (Model,), class_attrs)

    @staticmethod
    def execute_sql(connection: Connection, sql: str, success_message: str = "SQL statement committed.") -> None:
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

    @staticmethod
    def create_schema(connection, schema_name: str):
        """
        Checks if a schema exists and creates it if it doesn't.
        """
        logging.info(f"Creating schema: {schema_name}")
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

    @staticmethod
    def table_schema_matches(inspector: inspect, schema: str, table: str, model_class: DeclarativeBase) -> bool:
        """
        Check if the schema matches for a table.

        Args:
            inspector (inspect): The SQLAlchemy inspector object.
            schema (str): The schema name.
            table (str): The table name.
            model_class (DeclarativeBase): The SQLAlchemy model class.

        Returns:
            bool: True if the schema matches, False otherwise
        """
        logging.info(f"Checking if schema matches for table: {table} in schema: {schema}")
        existing_columns = Dict[str, Dict[str, Any]] = {
            col["name"]: col for col in inspector.get_columns(table, schema)
        }
        model_columns = Dict[str, Column] = {
            col.name: col for col in model_class.__table__.columns
        }

        # Check if the number of columns match
        if len(existing_columns) != len(model_columns):
            return False

        for col_name, column in model_columns.items():
            # Check if the column exists and has the same type
            if col_name not in existing_columns:
                return False
            # Check if the column type matches
            if str(existing_columns[col_name]["type"]) != str(column.type):
                return False

        return True

    def add_new_columns(
            self,
            connection: Connection,
            schema: str,
            table_name: str,
            model_columns: Dict[str, Any],
            existing_columns: Dict[str, Any],
    ) -> None:
        """
        Add new columns to the table.

        Args:
            connection (Connection): The SQLAlchemy connection.
            schema (str): The schema name.
            table_name (str): The table name.
            model_columns (Dict[str, Any]): The model columns.
            existing_columns (Dict[str, Any]): The existing

        Returns:
            None
        """
        for col_name, column in model_columns.items():
            if col_name not in existing_columns:
                column_creation: str = (
                    f"ALTER TABLE {schema}.{table_name} ADD COLUMN {col_name} {column.type}"
                )
                self.execute_sql(
                    connection,
                    column_creation,
                    f"Column {col_name} added to {table_name} in schema {schema}"
                )

    def remove_deleted_columns(
            self,
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
                if self.has_data(connection, schema, table_name, col_name):
                    if force:
                        column_deletion: str = (
                            f"ALTER TABLE {schema}.{table_name} DROP COLUMN {col_name}"
                        )
                        self.execute_sql(
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
                    self.execute_sql(
                        connection,
                        column_deletion,
                        f"Deleted column {col_name} from table {table_name}",
                    )

    @staticmethod
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
            self,
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
                    self.execute_sql(
                        connection,
                        alter_column,
                        f"Altered column {col_name} in table {table_name}",
                    )

    @staticmethod
    def create_table(connection: Connection, model_class: DeclarativeBase) -> None:
        """
        Create a new table based on the model.

        Args:
            connection (Connection): SQLAlchemy connection
            model_class (DeclarativeBase): SQLAlchemy model class
        """
        model_class.__table__.create(connection)
        logging.info("Created new table: %s", model_class.__tablename__)

    def build(self):
        """
        Build the workspace.
        """
        db_type = self.config.get("connection").get("type")
        db_connection = self.config.get("connection")
        del db_connection["type"]
        engine = self.get_connection(db_type=db_type, **db_connection)
        inspector = inspect(engine)

        with engine.begin() as connection:
            for table in self.generate_table_object():
                logging.info(f"Creating table: {table.__tablename__} in schema: {table.__schema__}")
                self.create_schema(connection, table.__schema__)
                if not inspector.has_table(table.__tablename__, schema=table.__schema__):
                    self.create_table(connection, table)
                    continue
