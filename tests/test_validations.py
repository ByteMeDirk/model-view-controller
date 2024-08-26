import unittest
from unittest.mock import patch

from model_view_controller.validations import validate_config_file, validate_table_file


class TestValidations(unittest.TestCase):

    @patch("model_view_controller.validations.logging")
    def test_validate_config_file_success(self, mock_logging):
        valid_config = {
            "context": {"environment": "dev"},
            "connection": {"type": "postgres"},
            "schemas": [{"name": "public"}],
        }
        validate_config_file(valid_config)
        mock_logging.info.assert_called_with("Config file validation successful.")

    @patch("model_view_controller.validations.logging")
    def test_validate_config_file_missing_context(self, mock_logging):
        invalid_config = {
            "connection": {"type": "postgres"},
            "schemas": [{"name": "public"}],
        }
        with self.assertRaises(ValueError):
            validate_config_file(invalid_config)
        mock_logging.error.assert_called()

    @patch("model_view_controller.validations.logging")
    def test_validate_config_file_invalid_connection(self, mock_logging):
        invalid_config = {
            "context": {"environment": "dev"},
            "connection": "invalid",
            "schemas": [{"name": "public"}],
        }
        with self.assertRaises(ValueError):
            validate_config_file(invalid_config)
        mock_logging.error.assert_called()

    @patch("model_view_controller.validations.logging")
    def test_validate_config_file_invalid_schemas(self, mock_logging):
        invalid_config = {
            "context": {"environment": "dev"},
            "connection": {"type": "postgres"},
            "schemas": "invalid",
        }
        with self.assertRaises(ValueError):
            validate_config_file(invalid_config)
        mock_logging.error.assert_called()

    @patch("model_view_controller.validations.logging")
    def test_validate_table_file_success(self, mock_logging):
        valid_table = {
            "name": "users",
            "description": "User table",
            "schema": "public",
            "columns": [{"name": "id", "type": "int"}],
        }
        validate_table_file(valid_table)
        mock_logging.info.assert_called_with("Table file validation successful.")

    @patch("model_view_controller.validations.logging")
    def test_validate_table_file_missing_name(self, mock_logging):
        invalid_table = {
            "description": "User table",
            "schema": "public",
            "columns": [{"name": "id", "type": "int"}],
        }
        with self.assertRaises(ValueError):
            validate_table_file(invalid_table)
        mock_logging.error.assert_called()

    @patch("model_view_controller.validations.logging")
    def test_validate_table_file_invalid_description(self, mock_logging):
        invalid_table = {
            "name": "users",
            "description": 123,  # Should be a string
            "schema": "public",
            "columns": [{"name": "id", "type": "int"}],
        }
        with self.assertRaises(ValueError):
            validate_table_file(invalid_table)
        mock_logging.error.assert_called()

    @patch("model_view_controller.validations.logging")
    def test_validate_table_file_invalid_schema(self, mock_logging):
        invalid_table = {
            "name": "users",
            "description": "User table",
            "schema": 123,  # Should be a string
            "columns": [{"name": "id", "type": "int"}],
        }
        with self.assertRaises(ValueError):
            validate_table_file(invalid_table)
        mock_logging.error.assert_called()

    @patch("model_view_controller.validations.logging")
    def test_validate_table_file_invalid_columns(self, mock_logging):
        invalid_table = {
            "name": "users",
            "description": "User table",
            "schema": "public",
            "columns": "invalid",  # Should be a list
        }
        with self.assertRaises(ValueError):
            validate_table_file(invalid_table)
        mock_logging.error.assert_called()


if __name__ == "__main__":
    unittest.main()
