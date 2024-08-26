import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from model_view_controller.config import (
    crawl_workspace,
    read_file,
    write_file,
    parse_file,
    compare_workspace_state_files,
    find_latest_workspace_state_version,
    read_and_parse_config,
    read_and_parse_workspace_files,
    generate_workspace_state_file,
)


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_content = """
            context:
              environment: dev
            connection:
                type: postgres
                host: localhost
                port: 5432
                user: postgres
                password: postgres
                database: postgres
            schemas:
              - name: public
                description: Default schema
              - name: customer
                description: Customer schema
              - name: product
                description: Product schema
        """
        self.user_content = """
            name: customer
            description: Customer table
            schema: {{ "dev_" if environment == "dev" else "" }}customer
            columns:
              - name: id
                type: int
                primary_key: true
              - name: name
                type: varchar
              - name: email
                type: varchar
              - name: dob
                type: date
        """
        with open(os.path.join(self.temp_dir, "config.yml"), "w") as f:
            f.write(self.config_content)
        with open(os.path.join(self.temp_dir, "user.yaml"), "w") as f:
            f.write(self.user_content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_crawl_workspace(self):
        config_file, other_files = crawl_workspace(self.temp_dir)
        self.assertTrue(config_file.endswith("config.yml"))
        self.assertEqual(len(other_files), 1)
        self.assertTrue(other_files[0].endswith("user.yaml"))

    def test_read_file(self):
        file_path = os.path.join(self.temp_dir, "config.yml")
        content = read_file(file_path)
        self.assertIn("context:", content)
        self.assertIn("connection:", content)

    def test_write_file(self):
        file_path = os.path.join(self.temp_dir, "test.txt")
        content = "Test content"
        written_path = write_file(file_path, content)
        self.assertEqual(written_path, file_path)
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_parse_file(self):
        file_string = "name: {{ name }}\nvalue: {{ value }}"
        context = {"name": "test", "value": 123}
        result = parse_file(file_string, context)
        self.assertEqual(result, {"name": "test", "value": 123})

    def test_compare_workspace_state_files(self):
        file1 = {"key1": "value1", "key2": "value2"}
        file2 = {"key1": "value1", "key2": "value3"}
        self.assertTrue(compare_workspace_state_files(file1, file2))
        self.assertFalse(compare_workspace_state_files(file1, file1))

    @patch("glob.glob")
    def test_find_latest_workspace_state_version(self, mock_glob):
        mock_glob.return_value = [
            "mvc_workspace_state_1.yaml",
            "mvc_workspace_state_2.yaml",
            "mvc_workspace_state_3.yaml",
        ]
        self.assertEqual(find_latest_workspace_state_version(), 4)

    def test_read_and_parse_config(self):
        config_file = os.path.join(self.temp_dir, "config.yml")
        config_data, context, connection = read_and_parse_config(config_file)
        self.assertIn("context", config_data)
        self.assertIn("connection", config_data)
        self.assertEqual(context["environment"], "dev")
        self.assertEqual(connection["type"], "postgres")

    def test_read_and_parse_workspace_files(self):
        workspace_files = [os.path.join(self.temp_dir, "user.yaml")]
        config_context = {"environment": "dev"}
        config_connection = {"database": "postgres"}
        result = read_and_parse_workspace_files(
            workspace_files, config_context, config_connection
        )
        self.assertIn("postgres.dev_customer.customer", result)
        self.assertEqual(result["postgres.dev_customer.customer"]["name"], "customer")

    @patch("model_view_controller.config.find_latest_workspace_state_version")
    @patch("model_view_controller.config.write_file")
    def test_generate_workspace_state_file(self, mock_write_file, mock_find_version):
        mock_find_version.return_value = 1
        mock_write_file.return_value = "mvc_workspace_state_1.yaml"
        result = generate_workspace_state_file(self.temp_dir)
        self.assertEqual(result, "mvc_workspace_state_1.yaml")


if __name__ == "__main__":
    unittest.main()
