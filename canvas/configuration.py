#	coding utf-8
'''
Loads the canvas configuration at `settings.json`,
and later updates it with plugin-set values.
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

CONFIG_FILE = 'settings.json'
LOG_LEVELS = [
	'debug',
	'info',
	'warning',
	'error',
	'critical'
]
ILLEGAL_OVERRIDES = [
	'active', 
	'logging',
	'database',
	'deferral'
]

def load():
	'''
	Load the initial configuration file
	'''
	config_path = os.path.join(CANVAS_HOME, CONFIG_FILE)
	with open(config_path, 'r') as f:
		config = json.load(f)
	
	log_config = config['logging']
	for_logger = {
		'level': (1 + LOG_LEVELS.index(log_config['level']))*10,
		'format': '%(asctime)s %(name)-30s %(levelname)-10s %(message)s'
	}
	if log_config['create_custom']:
		for_logger['filename'] = log_config['custom_path']
	logging.basicConfig(**for_logger)

	#	TODO: Bad
	if int(os.environ.get('CANVAS_PRINT_LOG', '0')) > 1:
		logging.addHandler(logging.StreamHandler(sys.stdout))

	return config

def update_from_plugins(config):
	'''
	Update the base config object with plugin-set values and
	wrap to replace `KeyError` with `ConfigKeyError`.
	'''

	from .core.plugins import get_path_occurrences

	def careful_updates(target, source):
		for key, val in source.items():
			if target is config and key in ILLEGAL_OVERRIDES:
				raise PluginConfigError(f'{key} cannot be set by a plugin')
			if not key in target:
				target[key] = val
				continue
			to_update = target[key]
			if isinstance(to_update, dict):
				careful_updates(to_update, val)
			else:
				target[key] = val

	for config_path in get_path_occurrences(CONFIG_FILE, include_base=False, filter=os.path.isfile):
		with open(config_path, 'r') as f:
			careful_updates(config, json.load(f))
	
	return WrappedDict(config, ConfigKeyError)
