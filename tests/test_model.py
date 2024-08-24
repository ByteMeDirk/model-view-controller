import os
import unittest

import yaml
from sqlalchemy import Column, Integer, String, Text

from model_view_controller.model import get_sqlalchemy_type, create_model_from_yaml, Model


class TestModel(unittest.TestCase):
    def setUp(self):
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets')

    def test_get_sqlalchemy_type(self):
        self.assertEqual(get_sqlalchemy_type('integer'), Integer)
        self.assertEqual(get_sqlalchemy_type('string', 50), String(50))
        self.assertEqual(get_sqlalchemy_type('text'), Text)

    def test_create_model_from_yaml(self):
        model_path = os.path.join(self.assets_dir, 'model1.yaml')
        with open(model_path, 'r') as f:
            yaml_config = yaml.safe_load(f)

        UserModel = create_model_from_yaml('users', 'public', yaml_config)
        self.assertEqual(UserModel.__tablename__, 'users')
        self.assertEqual(UserModel.__schema__, 'public')
        self.assertTrue(hasattr(UserModel, 'id'))
        self.assertTrue(hasattr(UserModel, 'username'))
        self.assertTrue(hasattr(UserModel, 'email'))

    def test_model_get_attributes(self):
        class TestModel(Model):
            __tablename__ = 'test_table'
            id = Column(Integer, primary_key=True)
            name = Column(String)

        model = TestModel()
        attributes = model.get_attributes()
        self.assertIn('id', attributes)
        self.assertIn('name', attributes)
