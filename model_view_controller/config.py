import glob
import logging
from textwrap import dedent
from typing import Dict, List, Tuple
from datetime import datetime
import yaml
from jinja2 import Template

from .validations import validate_config_file, validate_table_file

logging.basicConfig(level=logging.INFO)


def crawl_workspace(workspace_path: str) -> Tuple:
    """
    Crawls the workspace and returns the path to the config file and a list of the rest of the files.

    Args:
        workspace_path: The path to the workspace.

    Returns:
        Tuple: A tuple containing the path to the config file and a list of the rest of the files.
    """
    workspace_files: List = []
    for file in glob.glob(f"{workspace_path}/**/*", recursive=True):
        if file.endswith(('.yaml', '.yml')):
            workspace_files.append(file)
    logging.info(f"Workspace files: {workspace_files}")

    # Ensure only config.[yaml,yml] is in the directory AND that there is only one
    config_files = [file for file in workspace_files if "config." in file]
    if len(config_files) != 1:
        raise ValueError("There must be exactly one config.yaml file in the workspace.")
    logging.info(f"Config file: {config_files[0]}")

    # Return a string path to config file and return the rest non config file paths in a list
    return config_files[0], [file for file in workspace_files if file not in config_files]


def read_file(file_path: str) -> str:
    """
    Reads a file and returns an un-dented string.

    Args:
        file_path: Path to the file to read.

    Returns:
        str: The contents of the file.
    """
    logging.info(f"Reading file: {file_path}")
    with open(file_path, "r") as file:
        return dedent(file.read())


def write_file(file_path: str, file_string: str) -> str:
    """
    Writes a file string to a file.

    Args:
        file_path: The path to the file to write.
        file_string: The string to write to the file.

    Returns:
        str: The path to the file that was written.
    """
    logging.info(f"Writing file: {file_path}")
    with open(file_path, "w") as file:
        file.write(file_string)

    return file_path


def parse_file(file_string: str, context: [Dict, None] = None) -> Dict:
    """
    Parses a file string and returns a dictionary. If a context is provided, the file string is rendered with the context.

    Args:
        file_string: The file string to parse.
        context: The context to render the file string with.

    Returns:
        Dict: The parsed file string as a dictionary.
    """
    if context:
        template = Template(file_string)
        rendered_yaml = template.render(context)
        return yaml.safe_load(rendered_yaml)
    else:
        return yaml.safe_load(file_string)


def generate_workspace_state_file(workspace_path: str) -> str:
    """
    Get the workspace state file.

    Args:
        workspace_path: The path to the workspace.

    Returns:
        str: The path to the workspace state file.
    """
    # Get the path to the workspace state file
    config_file, workspace_files = crawl_workspace(
        workspace_path=workspace_path
    )

    # Read the config file and parse it
    logging.info(f"Reading config file: {config_file}")
    config_data: Dict = parse_file(file_string=read_file(file_path=config_file))
    validate_config_file(config_file=config_data) # Validate the config file
    config_data_context: Dict = config_data.get("context", {})
    config_data_connection: Dict = config_data.get("connection", {})

    # Read the workspace files and parse them
    logging.info(f"Reading workspace files: {workspace_files}")
    workspace_files_data: Dict = {}
    for workspace_file in workspace_files:
        workspace_file_data: Dict = parse_file(
            file_string=read_file(file_path=workspace_file),
            context=config_data_context
        )
        validate_table_file(table_file=workspace_file_data) # Validate the table file

        # Add database and table name to workspace_file_data
        workspace_file_data["database"] = config_data_connection.get("database")

        # ToDo: Ensure the table name and schema is not a duplicate
        table_path = f"{config_data_connection.get('database')}.{workspace_file_data.get('schema')}.{workspace_file_data.get('name')}"
        workspace_files_data[table_path] = workspace_file_data

    # Write the workspace state file as current epoch
    logging.info("Writing workspace state file.")
    workspace_state_file_path = write_file(
        file_path=f"mvc_workspace_state.yaml",
        file_string=yaml.dump(workspace_files_data)
    )

    return workspace_state_file_path
