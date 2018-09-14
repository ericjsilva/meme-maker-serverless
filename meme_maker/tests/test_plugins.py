import unittest

try:
    from unittest import mock
except ImportError:
    import mock

import os

from meme_maker.plugins import (
    Plugin,
    PluginMeta,
    PluginsLoader,
    PluginValidator
)

fake_meta = {
    #Required fake fields
    'name': 'fake',
    'version': 0,
    'scm': 'http://fake.git.repo',
    'script': 'fake.py',
    'handler': 'run',
    #Optional fake fields
    'author': 'Fake Author',
    'email': 'fake@email.co',

}


class PluginValidatorTestCase(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(PluginMeta, 'get_meta_content', return_value=fake_meta) as mock_method:
            self.validator = PluginValidator(fake_meta['name'])

    def test_pass_validation_on_meta_file_present(self):
        with mock.patch.object(os, 'listdir', return_value=[self.validator.default_meta_file]) as mock_method:
            self.assertTrue(self.validator.check_meta_file())

    def test_fail_validation_on_meta_file_absence(self):
        with mock.patch.object(os, 'listdir', return_value=[]) as mock_method:
            self.assertFalse(self.validator.check_meta_file())

    def test_pass_on_required_fields_present(self):
        self.assertTrue(self.validator.validate_required_fields())

    #def test_fail_on_required_fields_not_present(self):
    #    self.validator.plugin_meta_required.pop()
    #    self.assertTrue(self.validator.validate_required_fields())

    def test_fail_on_unsupported_fields_present(self):
        fake_meta['alien'] = None
        self.assertFalse(self.validator.validate_unsupported_fields())
        del(fake_meta['alien'])

    #def test_fail_on_handler_field_absence(self):
    #    self.assertFalse(self.validator.validate_handler())

    def test_if_is_valid_pass_plugins_meta_is_set(self):
        with mock.patch.object(os, 'listdir', return_value=[self.validator.default_meta_file]) as mock_method:
            with mock.patch.object(os.path, 'exists', return_value=True) as mock_method:
                self.validator.is_valid()
                self.assertDictEqual(self.validator.plugin.meta, fake_meta)


class PluginTestCase(unittest.TestCase):
    def setUp(self):
        self.plugin = Plugin()
        self.plugin.meta = fake_meta

    def test_name_attr_returns_meta_name(self):
        self.assertEqual(self.plugin.name, fake_meta['name'])

    def test_version_attr_returns_meta_version(self):
        self.assertEqual(self.plugin.version, fake_meta['version'])

    def test_scm_attr_returns_meta_scm(self):
        self.assertEqual(self.plugin.scm, fake_meta['scm'])

    def test_script_attr_returns_meta_script_without_extension(self):
        script, ext = fake_meta['script'].split('.')
        self.assertEqual(self.plugin.script, script)

    def test_author_attr_returns_meta_author(self):
        self.assertEqual(self.plugin.author, fake_meta['author'])

    def test_email_attr_returns_meta_email(self):
        self.assertEqual(self.plugin.email, fake_meta['email'])


class PluginMetaTestCase(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(PluginMeta, 'get_meta_content', return_value=fake_meta) as mock_method:
            self.meta = PluginMeta(fake_meta['name'])

    def test_get_plugin_path_returns_full_plugin_path_with_name(self):
        self.assertEqual(self.meta.get_plugin_path(),
            os.path.join(self.meta.plugins_path, fake_meta['name']))

    def test_get_meta_path_returns_full_default_meta_path(self):
        self.assertEqual(self.meta.get_meta_path(),
            os.path.join(self.meta.get_plugin_path(), self.meta.default_meta_file))

    def test_get_script_file_returns_full_script_path(self):
        self.assertEqual(self.meta.get_script_file(fake_meta['script']),
            os.path.join(self.meta.plugin_path, fake_meta['script']))


class PluginLoaderTestCase(unittest.TestCase):
    #TODO: Write more :-) PluginLoader tests
    pass

