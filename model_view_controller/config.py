import logging
from glob import glob

import yaml

logging.basicConfig(level=logging.INFO)


def read_yaml_file(file_path: str) -> dict:
    """
    Read a YAML file and return its contents.

    Args:
        file_path (str): Path to the YAML file

    Returns:
        dict: Contents of the YAML file
    """
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def get_model_configs(path: str) -> list:
    """
    Get all YAML model configuration files in the given path.

    Args:
        path (str): Directory path to search for model configs

    Returns:
        list: List of paths to model configuration files
    """
    files = []
    for model_file in glob(f"{path}/*.y*ml"):
        if model_file != f"{path}/config.yaml":
            files.append(model_file)
    logging.info("Found %s models in path: %s", len(files), path)
    return files


def get_config(path: str) -> dict:
    """
    Get the main configuration from the config.yaml file.

    Args:
        path (str): Directory path containing the config.yaml file

    Returns:
        dict: Configuration data

    Raises:
        FileNotFoundError: If config.yaml is not found in the given path
    """
    config_path = f"{path}/config.yaml"
    try:
        return read_yaml_file(config_path)
    except FileNotFoundError:
        logging.error("config.yaml not found in path: %s", path)
        raise
