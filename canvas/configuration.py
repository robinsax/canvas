#	coding utf-8
'''
Configuration storage and management.
'''

import os
import logging

from .namespace import export
from .core.json_io import deserialize_json
from .core.dictionaries import Configuration
from . import __home__

config = Configuration()
export('config')(config)

@export
def plugin_config(plugin_name):
	from .core.plugins import plugin_base_path

	config_path = os.path.join(plugin_base_path(plugin_name), 'settings.json')
	with open(config_path, 'r') as config_file:
		plugin_config = Configuration(deserialize_json(config_file.read()))
		
	if plugin_name in config.plugins:
		def update_section(source, dest):
			for key, value in source.items():
				if isinstance(value, Configuration):
					update_section(value, dest[key])
				else:
					dest[key] = value

		update_section(config.plugins[plugin_name], plugin_config)

	return plugin_config

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
