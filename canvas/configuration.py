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
	'finalize',
	'write'
]

#	The name of the configuration file.
CONFIG_FILE = 'settings.json'
#	Allowed values of the `log_level` configuration entry.
LOG_LEVELS = [
	'debug',
	'info',
	'warning',
	'error',
	'critical'
]
#	Root configuration entries which plugins are not allowed to modify (because 
#	they have already been read).
ILLEGAL_OVERRIDES = [
	'active', 
	'logging',
	'database'
]

def load(configure_logger=True):
	'''
	Load and return the initial configuration.
	'''
	#	Read the configuration file.
	config_path = os.path.join(CANVAS_HOME, CONFIG_FILE)
	with open(config_path, 'r') as f:
		config = json.load(f)

	if not configure_logger:
		return config
	
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

	#	Return the loaded configuration storage object.
	return config

def finalize(config):
	'''
	Update a configuration object with plugin-overridden values and wrap to 
	replace `KeyError` with an object-specific error.
	'''
	#	This import is only safe after the core has been initialized, which 
	#	happens after this module is imported.
	from .core.plugins import get_path_occurrences

	def careful_updates(target, source):
		'''
		Update the dictionary `target` with the contents of `source`, recursing
		on sub-dictionaries to allow intutative override behavior.
		'''
		for key, val in source.items():
			if target is config and key in ILLEGAL_OVERRIDES:
				#	Illegal override performed.
				raise PluginConfigError(f'{key} cannot be set by a plugin')
			if key == 'client_dependencies':
				target_dict = config['client_dependencies']
				#	Plugins need to register their client dependencies without 
				#	considering other loaded plugins (or the core). Therefore 
				#	the global dependency lists are configured additively.
				if 'dependencies' in val:
					for d in val['dependencies']:
						if d not in target_dict['dependencies']:
							target_dict['dependencies'].append(d)
				if 'library_dependencies' in val:
					for d in val['library_dependencies']:
						if d not in target_dict['library_dependencies']:
							target_dict['library_dependencies'].append(d)
				if 'font_dependencies' in val:
					target_dict['font_dependencies'].update(val['font_dependencies'])
				if 'icon_dependency' in val:
					target_dict['icon_dependency'] = val['icon_dependency']
				continue
			if not key in target:
				#	Not overriding, update normally.
				target[key] = val
				continue
			
			#	Recurse if the target contains a dictionary under this key.
			to_update = target[key]
			if isinstance(to_update, dict):
				careful_updates(to_update, val)
			else:
				#	Override the value normally.
				target[key] = val

	#	Read all plugin configuration file instances, updating the 
	#	configuration with their contents.
	for config_path in get_path_occurrences(CONFIG_FILE, include_base=False, filter=os.path.isfile):
		with open(config_path, 'r') as f:
			careful_updates(config, json.load(f))
	
	#	Wrap and return the resulting configuration object.
	return WrappedDict(config, ConfigKeyError)

def write(config):
	'''
	Write the configuration file.
	'''
	#	Read the configuration file.
	config_path = os.path.join(CANVAS_HOME, CONFIG_FILE)
	with open(config_path, 'w') as f:
		#	Use tabs you barbarian!
		f.write(json.dumps(config, indent=4).replace('    ', '\t'))