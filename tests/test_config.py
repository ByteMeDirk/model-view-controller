import unittest
import os
from unittest.mock import patch
from model_view_controller.config import read_yaml_file, get_model_configs, get_config

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets')

    def test_read_yaml_file(self):
        config_path = os.path.join(self.assets_dir, 'config.yaml')
        result = read_yaml_file(config_path)
        self.assertIn('database', result)
        self.assertEqual(result['database']['connection'], 'sqlite:///:memory:')

    def test_get_model_configs(self):
        result = get_model_configs(self.assets_dir)
        self.assertEqual(len(result), 2)
        self.assertIn('user.yaml', result[0])
        self.assertIn('posts.yaml', result[1])

    def test_get_config(self):
        result = get_config(self.assets_dir)
        self.assertIn('database', result)
        self.assertEqual(result['database']['schema'], 'public')

    def test_get_config_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            get_config('/nonexistent/path')