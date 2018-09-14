#!/usr/bin/env python
import os
import logging
import importlib

import yaml

logger = logging.getLogger('meme.plugins')
logger.setLevel(logging.INFO)


class Plugin(object):
    def __init__(self):
        self.meta = None
        self.module = None

    @property
    def handler(self):
        handler_name = self.meta.get('handler')
        try:
            return getattr(self.module, handler_name)
        except Exception as exc:
            print(exc)
            return

    @property
    def name(self):
        return self.meta.get('name')

    @property
    def version(self):
        return self.meta.get('version')

    @property
    def scm(self):
        return self.meta.get('scm')

    @property
    def script(self):
        script, ext = self.meta.get('script').split('.')
        return script

    @property
    def author(self):
        return self.meta.get('author')

    @property
    def email(self):
        return self.meta.get('email')

    def __str__(self):
        return '<Plugin: {}>'.format(self.name)


class PluginMeta(object):
    default_meta_file = 'plugin.yaml'

    plugins_path = os.path.dirname(
        os.path.abspath(__file__)
    )

    plugin_meta_required = [
        'name', 'version', 'scm', 'script', 'handler'
    ]

    plugin_meta_optional = [
        'author', 'email'
    ]

    def __init__(self, plugin):
        self.plugin_name = plugin
        self.plugin_path = self.get_plugin_path()
        self.meta_path = self.get_meta_path()
        self.meta_content = self.get_meta_content()

    def get_plugin_path(self):
        return os.path.join(self.plugins_path, self.plugin_name)

    def get_meta_path(self):
        return os.path.join(self.plugin_path, self.default_meta_file)

    def get_meta_content(self):
        with open(self.meta_path, 'r') as meta_file:
            try:
                return yaml.load(meta_file)
            except yaml.YAMLError as exc:
                raise

    def get_script_file(self, script_name):
        return os.path.join(self.plugin_path, script_name)


# TODO: More validation
class PluginValidator(PluginMeta):
    def __init__(self, plugin_name):
        super(PluginValidator, self).__init__(plugin_name)
        self.plugin = Plugin()
        self.errors = []

    def check_meta_file(self):
        plugin_package = os.listdir(self.plugin_path)
        if self.default_meta_file not in plugin_package:
            self.errors.append(
                'Missing meta file {}'.format(self.default_meta_file))
            return False
        return True

    def validate_required_fields(self):
        common_fields = set(self.plugin_meta_required) & set(
            self.meta_content.keys())
        missing_fields = set(self.plugin_meta_required) - set(
            self.meta_content.keys())
        if len(common_fields) < len(self.plugin_meta_required):
            self.errors.append(
                'Missing required fields: {}'.format(missing_fields))
            return False
        return True

    def validate_unsupported_fields(self):
        unsupported_fields = set(self.meta_content.keys()) - set(
            self.plugin_meta_required + self.plugin_meta_optional)
        if len(unsupported_fields):
            self.errors.append(
                'Unsupported field: {}'.format(unsupported_fields))
            return False
        return True

    def validate_script_file(self):
        script_name = self.meta_content.get('script')
        if not script_name:
            self.errors.append('Missing value of required parameter script')
            return False
        script_file = self.get_script_file(script_name)
        if not os.path.exists(script_file):
            self.errors.append('Missing script file: {}'.format(script_file))
            return False
        return True

    def validate_handler(self):
        handler_name = self.meta_content.get('handler')
        if not handler_name:
            self.errors.append('Missing value of required parameter handler')
            return False
        return True

    def is_valid(self):
        validators = [
            self.validate_required_fields,
            self.validate_unsupported_fields,
            self.check_meta_file,
            self.validate_script_file,
            self.validate_handler
        ]
        for validator in validators:
            if not validator():
                return False
        self.plugin.meta = self.meta_content
        return True


class PluginContext(object):
    def __init__(self, meme, handler, args, kwargs):
        self.meme = meme
        self.handler = handler
        self.args = args
        self.kwargs = kwargs
        self.logger = logger

        self.result = None
        self.event = None

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return '<PluginContext: {}>'.format(self.event)


class PluginsLoader(PluginMeta):
    """ Plugin loader for Meme-Maker.

        Initialization:
            plugins = PluginsLoader()
            plugins.discover()

        Dispatch event:

            @plugins.dispatch
            def some_meme_method(self):
                ...

        Receive event:
            def some_plugin_method(context):
                context.logger.info(context.to_dict())
    """

    def __init__(self):
        self.plugins = {}

    def handle(self, plugin_name, context):
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return {'error': 'Plugin {} not found'.format(plugin_name)}
        try:
            return {'response': plugin.handler(context)}
        except Exception as exc:
            return {'exception': exc}

    def discover(self):
        if not os.path.exists(self.plugins_path):
            logger.error(
                'Unable to resolve plugins path: {}'.format(self.plugins_path))
            return
        self.load()

    def __prepare(self, plugins):
        for plugin in plugins:
            logger.info('Checking plugin: {}'.format(plugin))
            plugin_validator = PluginValidator(plugin)

            if plugin_validator.is_valid():
                yield plugin_validator.plugin
            else:
                logger.warning('Plugin {} is invalid'.format(plugin))
                for error in plugin_validator.errors:
                    logger.error(error)

    def load(self):
        plugins = [
            plugin
            for plugin in os.listdir(self.plugins_path)
            if os.path.isdir(os.path.join(self.plugins_path, plugin))
            and plugin != '__pycache__'
        ]
        try:
            for plugin in self.__prepare(plugins):
                plugin.module = importlib.import_module(
                    '.'.join([__name__, plugin.name, plugin.script]))
                self.plugins[plugin.name] = plugin
        except ImportError as exc:
            logger.error('Unable to load plugins: {}'.format(exc))

    def _dispatch_event(self, context, event):
        for plugin in self.plugins:
            context.event = '{}_{}'.format(event, context.handler.__name__)
            self.handle(plugin, context)

    def dispatch(self, handler):
        def wrapper(meme, *args, **kwargs):
            context = PluginContext(meme, handler, args, kwargs)
            self._dispatch_event(context, 'pre')
            context.result = handler(meme, *args, **kwargs)
            self._dispatch_event(context, 'post')
            return context.result

        return wrapper


def subscribe(events):
    def real_decorator(fn):
        def wrapper(context):
            if context.event in events:
                return fn(context)

        return wrapper

    return real_decorator
