#	coding utf-8
'''
Plugin management.
'''

import os
import sys

from ..namespace import export
from ..utils import logger
from ..configuration import config
from .. import HOME

log = logger(__name__)

def plugin_base_path(name):
	return os.path.join(HOME, config.plugins.directory, 'canvas-pl-%s'%name)

def load_plugins():
	from .. import plugins as plugins_namespace

	for plugin in config.plugins.activated:
		path = plugin_base_path(plugin)
		sys.path.insert(0, path)

		log.info('Loading plugin: %s', plugin)
		try:
			plugins_namespace.__path__.append(path)
			__import__('canvas.plugins.%s'%plugin)
		except ModuleNotFoundError:
			log.critical('Plugin not found: %s', plugin)

@export
def get_path_occurrences(*path_parts, include_base=True, dir=False):
	path = os.path.join(*path_parts)
	occurrences = []
	path_check = os.path.isdir if dir else os.path.isfile
	
	for plugin in reversed(config.plugins.activated):
		path = os.path.join(plugin_base_path(plugin), path)
		if path_check(path):
			occurrences.insert(0, path)
	
	if include_base:
		base_instance_path = os.path.join(HOME, 'canvas', path)
		if path_check(base_instance_path):
			occurrences.insert(0, base_instance_path)

	return occurrences
