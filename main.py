import jinja2
import yaml
from jinja2 import Template

from model_view_controller.config import generate_workspace_state_file


def main():
    generate_workspace_state_file("mvc_customer")

if __name__ == "__main__":
    main()