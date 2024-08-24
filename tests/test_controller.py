import unittest
import os
from unittest.mock import Mock, patch
from sqlalchemy import create_engine, inspect, Integer, String
from sqlalchemy.orm import declarative_base

from model_view_controller import create_model_from_yaml
from model_view_controller.controller import Controller, table_schema_matches
from model_view_controller.config import read_yaml_file


class TestController(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        self.connection = self.engine.connect()
        self.Base = declarative_base()
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")

    def tearDown(self):
        self.connection.close()

    def test_build(self):
        model_path = os.path.join(self.assets_dir, "user.yaml")
        yaml_config = read_yaml_file(model_path)
        TestModel = create_model_from_yaml("users", "public", yaml_config, self.Base)

        Controller.build(self.connection, TestModel)
        inspector = inspect(self.engine)
        self.assertTrue(inspector.has_table("users"))

    def test_destroy(self):
        model_path = os.path.join(self.assets_dir, "user.yaml")
        yaml_config = read_yaml_file(model_path)
        TestModel = create_model_from_yaml("users", "public", yaml_config, self.Base)

        Controller.build(self.connection, TestModel)
        Controller.destroy(self.connection, TestModel)
        inspector = inspect(self.engine)
        self.assertFalse(inspector.has_table("users"))

    @patch("model_view_controller.controller.inspect")
    def test_table_schema_matches(self, mock_inspect):
        mock_inspector = Mock()
        mock_inspector.get_columns.return_value = [
            {"name": "id", "type": Integer()},
            {"name": "username", "type": String(50)},
            {"name": "email", "type": String(100)},
        ]
        mock_inspect.return_value = mock_inspector

        model_path = os.path.join(self.assets_dir, "user.yaml")
        yaml_config = read_yaml_file(model_path)
        TestModel = create_model_from_yaml("users", "public", yaml_config, self.Base)

        result = table_schema_matches(mock_inspector, "public", "users", TestModel)
        self.assertTrue(result)
