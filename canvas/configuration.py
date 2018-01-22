#	coding utf-8
'''
Configuration management.
'''

import os
import sys
import json
import logging

from . import CANVAS_HOME
from .exceptions import PluginConfigError, ConfigKeyError
from .utils import WrappedDict

__all__ = [
	'load',
	'update_from_plugins',
	'configure_logging'
]

#	The configuration file name.
CONFIG_FILE = 'settings.json'
#	Allowed values of the `log_level` 
#	configuration entry.
LOG_LEVELS = [
	'debug',
	'info',
	'warning',
	'error',
	'critical'
]
#	Root configuration entries which plugins
#	are not allowed to modify (because they
#	have already been read).
ILLEGAL_OVERRIDES = [
	'active', 
	'logging',
	'database',
	'deferral'
]

def load():
	'''
	Load and return the initial configuration.
	'''
	#	Read the configuration file.
	config_path = os.path.join(CANVAS_HOME, CONFIG_FILE)
	with open(config_path, 'r') as f:
		config = json.load(f)
	
	#	Configure the logging module.
	log_config = config['logging']
	for_logger = {
		'level': (1 + LOG_LEVELS.index(log_config['level']))*10,
		'format': '%(asctime)s %(name)-30s %(levelname)-10s %(message)s'
	}
	if log_config['create_custom']:
		#	Enable logging to a custom log file.
		for_logger['filename'] = log_config['custom_path']
	logging.basicConfig(**for_logger)

	#	Return the loaded configuration storage 
	#	object.
	return config

def update_from_plugins(config):
	'''
	Update a configuration object with plugin-overridden 
	values and wrap to replace `KeyError` with a more
	specific error.
	'''
	#	This import is only safe after the core has
	#	been initialized, which happens after this module
	#	is imported.
	from .core.plugins import get_path_occurrences

	def careful_updates(target, source):
		'''
		Update the dictionary `target` with the contents
		of `source`, recursing on sub-dictionaries to allow
		intutative override behavior.
		'''
		for key, val in source.items():
			if target is config and key in ILLEGAL_OVERRIDES:
				#	Illegal override performed.
				raise PluginConfigError(f'{key} cannot be set by a plugin')
			if key == 'client_dependencies':
				#	Plugins need to register their client dependencies 
				#	without considering other loaded plugins (or the 
				#	core). Therefore the global dependency lists are
				#	configured additively.
				config['client_dependencies']['dependencies'] += val['dependencies']
				config['client_dependencies']['library_dependencies'] += val['library_dependencies']
				continue
			if not key in target:
				#	Not overriding, update normally.
				target[key] = val
				continue
			
			#	Recurse if the target contains a dictionary under
			#	this key.
			to_update = target[key]
			if isinstance(to_update, dict):
				careful_updates(to_update, val)
			else:
				#	Override the value normally.
				target[key] = val

	#	Read all plugin configuration file instances, updating
	#	the configuration with their contents.
	for config_path in get_path_occurrences(CONFIG_FILE, include_base=False, filter=os.path.isfile):
		with open(config_path, 'r') as f:
			careful_updates(config, json.load(f))
	
	#	Wrap and return the resulting configuration object.
	return WrappedDict(config, ConfigKeyError)
