#	coding utf-8
'''
Configuration storage and management.
'''

import os
import pprint
import logging

from .namespace import export
from .core.json_io import deserialize_json
from .core.dictionaries import Configuration
from .utils import logger
from . import __home__

_importer_configs = dict()

config = Configuration()
export('config')(config)

@export
def plugin_config(plugin_name):
	from .core.plugins import plugin_base_path

	plugin_name = plugin_name.split('.')[-1]

	config_path = os.path.join(plugin_base_path(plugin_name), 'plugin.json')
	with open(config_path, 'r') as config_file:
		plugin_config = Configuration(deserialize_json(config_file.read()))

	def update_section(source, dest):
		for key, value in source.items():
			if isinstance(value, dict):
				update_section(value, dest[key])
			else:
				dest[key] = value

	if plugin_name in _importer_configs:
		update_section(_importer_configs[plugin_name], plugin_config)
	if plugin_name in config.plugins:
		update_section(config.plugins[plugin_name], plugin_config)
	
	#	Update the core.
	if 'core' in plugin_config:
		update_section(plugin_config.core, config)
	
	return plugin_config

def add_importer_config(target_name, content):
	_importer_configs[target_name] = content

def load_config():
	with open(os.path.join(__home__, 'settings.json'), 'r') as config_file:
		local_config = deserialize_json(config_file.read())

	for key, value in local_config.items():
		config[key] = value

	log_levels = ['debug', 'info', 'warning', 'error', 'critical']
	logging.basicConfig(
		level=(1 + log_levels.index(config.development.log_level))*10,
		format='%(asctime)s %(name)-30s %(levelname)-10s %(message)s'
	)
