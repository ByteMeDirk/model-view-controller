import logging
from typing import Dict

import yaml
from sqlalchemy import create_engine, Engine, Table, MetaData, Column, inspect, text
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base

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

    def create_schema(self, connection, schema_name: str):
        """
        Checks if a schema exists and creates it if it doesn't.
        """
        logging.info(f"Creating schema: {schema_name}")
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

    def build(self):
        """
        Build the workspace.
        """
        db_type = self.config.get("connection").get("type")
        db_connection = self.config.get("connection")
        del db_connection["type"]
        engine = self.get_connection(db_type=db_type, **db_connection)
        inspect(engine)

        with engine.begin() as connection:
            for table in self.generate_table_object():
                logging.info(f"Creating table: {table.__tablename__} in schema: {table.__schema__}")
                self.create_schema(connection, table.__schema__)
                table.__table__.create(connection)
