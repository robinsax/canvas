# coding: utf-8
'''
Configuration loading and management. canvas's core configuration file is
`settings.json`. Instances of `plugin.json` in activated plugins have the
ability to override both the core configuration and the configuration of
subsequently included plugins.

The core configuration is exposed as `config` in the root namespace. Plugins
should access their configuration via the `plugin_config` function.
'''

import os
import logging

from .json_io import deserialize_json
from .dictionaries import Configuration
from .utils import logger
from . import __home__

#	A plugin name to configuration override map for tracking plugin overrides
#	of other plugins.
_importer_overrides = dict()

def add_importer_config(target_plugin_name, override):
	'''Add an importer override.'''
	_importer_overrides[target_plugin_name] = override

#	Create the configuration object.
config = Configuration()

def plugin_config(plugin_name):
	'''
	Return the configuration for `plugin_name` with all overrides applied.
	Priority is given to the primary `settings.json` configuration, then any
	overrides by other plugins, then the default plugin configuration itself.
	'''
	#	This import would is circular since the plugin manager needs access to
	#	the global configuration and add_importer_config.
	from .core.plugins import plugin_base_path

	#	Since plugins are imported into the `canvas.plugins` package, the
	#	value of __name__ must be truncated.
	plugin_name = plugin_name.split('.')[-1]

	#	Load this plugin's plugin.json.
	config_path = os.path.join(plugin_base_path(plugin_name), 'plugin.json')
	with open(config_path, 'r') as config_file:
		plugin_config = Configuration(deserialize_json(config_file.read()))

	#	A lazy update algorithm suitable for selective overrides.
	def update_section(source, dest):
		for key, value in source.items():
			if isinstance(value, dict):
				update_section(value, dest[key])
			else:
				dest[key] = value

	#	Apply overrides.
	if plugin_name in _importer_configs:
		update_section(_importer_configs[plugin_name], plugin_config)
	if plugin_name in config.plugins:
		update_section(config.plugins[plugin_name], plugin_config)
	
	#	Allow the plugin to update the core configuration.
	if 'core' in plugin_config:
		update_section(plugin_config.core, config)
	
	return plugin_config

def load_config():
	'''Load the core configuration and apply its logging configuration.'''
	#	Load settings.json onto the core configuration.
	with open(os.path.join(__home__, 'settings.json'), 'r') as config_file:
		local_config = deserialize_json(config_file.read())
	for key, value in local_config.items():
		config[key] = value

	#	Apply logging configuration.
	log_levels = ['debug', 'info', 'warning', 'error', 'critical']
	logging.basicConfig(
		level=(1 + log_levels.index(config.development.log_level))*10,
		format='%(asctime)s %(name)-30s %(levelname)-10s %(message)s'
	)
