from sqlalchemy import Column, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from sqlalchemy import types


def get_sqlalchemy_type(yaml_type, length=None):
    """
    Get SQLAlchemy type based on YAML type string.

    Args:
        yaml_type (str): Type specified in YAML
        length (int, optional): Length for string types

    Returns:
        SQLAlchemy type
    """
    type_mapping = {
        name.lower(): getattr(types, name)
        for name in dir(types)
        if isinstance(getattr(types, name), type)
        and issubclass(getattr(types, name), types.TypeEngine)
    }

    # Add aliases and special cases
    type_mapping.update(
        {
            "int": types.Integer,
            "integer": types.Integer,
            "bigint": types.BigInteger,
            "smallint": types.SmallInteger,
            "string": types.String,
            "text": types.Text,
            "float": types.Float,
            "real": types.REAL,
            "double": types.Float,
            "decimal": types.DECIMAL,
            "numeric": types.Numeric,
            "datetime": types.DateTime,
            "timestamp": types.TIMESTAMP,
            "time": types.Time,
            "date": types.Date,
            "binary": types.LargeBinary,
            "large_binary": types.LargeBinary,
            "boolean": types.Boolean,
            "bool": types.Boolean,
            "unicode": types.Unicode,
            "unicode_text": types.UnicodeText,
        }
    )

    yaml_type = yaml_type.lower()
    if yaml_type == "string" and length:
        return types.String(length)

    return type_mapping.get(yaml_type, types.String)


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


def create_model_from_yaml(
    table_name: str, schema: str, yaml_config: dict, base_model=Model
):
    """
    Create a SQLAlchemy model from YAML configuration.

    Args:
        table_name (str): Name of the table
        schema (str): Database schema
        yaml_config (dict): YAML configuration for the model
        base_model: Base model class (default: Model)

    Returns:
        SQLAlchemy model class
    """
    metadata = MetaData(schema=schema)
    columns = []

    for column in yaml_config["columns"]:
        column_type = get_sqlalchemy_type(column["type"], column.get("length"))
        column_args = {
            "name": column["name"],
            "type_": column_type,
            "primary_key": column.get("primary_key", False),
        }
        if column.get("auto_increment"):
            column_args["autoincrement"] = True
        columns.append(Column(**column_args))

    table = Table(
        table_name, metadata, *columns, comment=yaml_config.get("description", "")
    )

    class_attrs = {
        "__table__": table,
        "__tablename__": table_name,
        "__schema__": schema,
    }

    return type(yaml_config.get("name", "CustomModel"), (base_model,), class_attrs)
