import glob
import logging
from textwrap import dedent
from typing import Dict, List, Tuple, Optional

import yaml
from jinja2 import Template

from .validations import validate_config_file, validate_table_file

logging.basicConfig(level=logging.INFO)


def crawl_workspace(workspace_path: str) -> Tuple[str, List[str]]:
    """
    Crawl the workspace and return the path to the config file and a list of other files.

    Args:
        workspace_path (str): The path to the workspace.

    Returns:
        Tuple[str, List[str]]: A tuple containing the path to the config file and a list of other files.

    Raises:
        ValueError: If there isn't exactly one config file in the workspace.
    """
    workspace_files = [
        file
        for file in glob.glob(f"{workspace_path}/**/*", recursive=True)
        if file.endswith((".yaml", ".yml"))
    ]
    logging.info(f"Workspace files: {workspace_files}")

    config_files = [file for file in workspace_files if "config." in file]
    if len(config_files) != 1:
        raise ValueError("There must be exactly one config.yaml file in the workspace.")

    config_file = config_files[0]
    logging.info(f"Config file: {config_file}")

    other_files = [file for file in workspace_files if file != config_file]
    return config_file, other_files


def read_file(file_path: str) -> str:
    """
    Read a file and return its contents as an un-dented string.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        str: The contents of the file.
    """
    logging.info(f"Reading file: {file_path}")
    with open(file_path, "r") as file:
        return dedent(file.read())


def write_file(file_path: str, file_string: str) -> str:
    """
    Write a string to a file.

    Args:
        file_path (str): The path to the file to write.
        file_string (str): The string to write to the file.

    Returns:
        str: The path to the file that was written.
    """
    logging.info(f"Writing file: {file_path}")
    with open(file_path, "w") as file:
        file.write(file_string)
    return file_path


def parse_file(file_string: str, context: Optional[Dict] = None) -> Dict:
    """
    Parse a file string and return a dictionary.

    Args:
        file_string (str): The file string to parse.
        context (Optional[Dict]): The context to render the file string with.

    Returns:
        Dict: The parsed file string as a dictionary.
    """
    if context:
        template = Template(file_string)
        rendered_yaml = template.render(context)
        return yaml.safe_load(rendered_yaml)
    return yaml.safe_load(file_string)


def compare_workspace_state_files(current_file: Dict, previous_file: Dict) -> bool:
    """
    Compare the previous version file to the current one.

    Args:
        current_file (Dict): The current file.
        previous_file (Dict): The previous file.

    Returns:
        bool: True if the files are different, False if they are the same.
    """
    return current_file != previous_file


def find_latest_workspace_state_version() -> int:
    """
    Find the most recent workspace state file version.

    Returns:
        int: The latest version number, or 1 if no files are found.
    """
    versions = [
        int(file.split("_")[-1].split(".")[0])
        for file in glob.glob("mvc_workspace_state_*.yaml")
    ]
    return max(versions) + 1 if versions else 1


def read_and_parse_config(config_file: str) -> Tuple[Dict, Dict, Dict]:
    """
    Read and parse the config file.

    Args:
        config_file (str): Path to the config file.

    Returns:
        Tuple[Dict, Dict, Dict]: A tuple containing the full config data, context data, and connection data.
    """
    logging.info(f"Reading config file: {config_file}")
    config_data = parse_file(file_string=read_file(file_path=config_file))
    validate_config_file(config_file=config_data)
    return (
        config_data,
        config_data.get("context", {}),
        config_data.get("connection", {}),
    )


def read_and_parse_workspace_files(
    workspace_files: List[str], config_context: Dict, config_connection: Dict
) -> Dict:
    """
    Read and parse the workspace files.

    Args:
        workspace_files (List[str]): List of workspace file paths.
        config_context (Dict): The context data from the config file.
        config_connection (Dict): The connection data from the config file.

    Returns:
        Dict: A dictionary containing the parsed workspace file data.
    """
    logging.info(f"Reading workspace files: {workspace_files}")
    workspace_files_data = {}
    for workspace_file in workspace_files:
        workspace_file_data = parse_file(
            file_string=read_file(file_path=workspace_file), context=config_context
        )
        validate_table_file(table_file=workspace_file_data)
        workspace_file_data["database"] = config_connection.get("database")
        table_path = f"{config_connection.get('database')}.{workspace_file_data.get('schema')}.{workspace_file_data.get('name')}"
        workspace_files_data[table_path] = workspace_file_data
    return workspace_files_data


def generate_workspace_state_file(workspace_path: str) -> str:
    """
    Generate the workspace state file.

    Args:
        workspace_path (str): The path to the workspace.

    Returns:
        str: The path to the generated workspace state file.
    """
    config_file, workspace_files = crawl_workspace(workspace_path)
    config_data, config_context, config_connection = read_and_parse_config(config_file)
    workspace_files_data = read_and_parse_workspace_files(
        workspace_files, config_context, config_connection
    )

    state_version = find_latest_workspace_state_version()

    if state_version > 1:
        previous_file_path = f"mvc_workspace_state_{state_version - 1}.yaml"
        previous_data = yaml.safe_load(read_file(file_path=previous_file_path))
        if not compare_workspace_state_files(workspace_files_data, previous_data):
            logging.info(
                f"No changes detected. Using existing state file: {previous_file_path}"
            )
            return previous_file_path

    new_file_path = f"mvc_workspace_state_{state_version}.yaml"
    logging.info(f"Writing new workspace state file: {new_file_path}")
    return write_file(
        file_path=new_file_path, file_string=yaml.dump(workspace_files_data)
    )
