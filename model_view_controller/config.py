import logging
from glob import glob
from typing import Dict, List, Any

import yaml

logging.basicConfig(level=logging.INFO)


def read_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Read a YAML file and return its contents.

    Args:
        file_path (str): Path to the YAML file

    Returns:
        Dict[str, Any]: Contents of the YAML file
    """
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def get_model_configs(path: str) -> List[str]:
    """
    Get all YAML model configuration files in the given path.

    Args:
        path (str): Directory path to search for model configs

    Returns:
        List[str]: List of paths to model configuration files
    """
    files: List[str] = []
    for model_file in glob(f"{path}/*.y*ml"):
        if model_file != f"{path}/config.yaml":
            files.append(model_file)
    logging.info("Found %s models in path: %s", len(files), path)
    return files


def get_config(path: str) -> Dict[str, Any]:
    """
    Get the main configuration from the config.yaml file.

    Args:
        path (str): Directory path containing the config.yaml file

    Returns:
        Dict[str, Any]: Configuration data

    Raises:
        FileNotFoundError: If config.yaml is not found in the given path
    """
    config_path: str = f"{path}/config.yaml"
    try:
        return read_yaml_file(config_path)
    except FileNotFoundError:
        logging.error("config.yaml not found in path: %s", path)
        raise
