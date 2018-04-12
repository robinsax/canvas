#	coding utf-8
'''
Plugin management.
'''

import os
import re
import sys
import traceback

from ..exceptions import DependencyError
from ..namespace import export
from ..utils import logger
from ..configuration import config, add_importer_config
from .. import __home__
from .json_io import deserialize_json

log = logger(__name__)

@export
def plugin_base_path(name):
	name = name.split('.')[-1]
	return os.path.join(__home__, config.plugins.directory, 'cvpl-%s'%name)

def load_plugins():
	from .. import plugins as plugins_namespace

	def load_plugin(name, dependency_of=None):
		path = plugin_base_path(name)
		config_path = os.path.join(path, 'plugin.json')

		if os.path.exists(config_path):
			with open(config_path) as config_file:
				raw_plugin_config = deserialize_json(config_file.read())
				if 'dependencies' in raw_plugin_config:
					dependencies = raw_plugin_config['dependencies']
				else:
					dependencies = tuple()
			
			for dependency in dependencies:
				if isinstance(dependency, (tuple, list)):
					dependency, importer_config = dependency
					add_importer_config(dependency, importer_config)
				load_plugin(dependency, name)

		sys.path.insert(0, path)

		plugin_label = name
		if dependency_of:
			plugin_label = '%s (from %s)'%(plugin_label, dependency_of)
		log.info('Loading plugin: %s', plugin_label)
		try:
			plugins_namespace.__path__.append(path)
			__import__('canvas.plugins.%s'%name)
		except ModuleNotFoundError as ex:
			length = len(list(traceback.walk_tb(ex.__traceback__)))
			if length == 1:
				raise DependencyError('Plugin not found: %s'%plugin_label)
			raise ex

	for plugin in config.plugins.activated:
		load_plugin(plugin)

#	TODO: Make descending and export ext.
@export
def get_path_occurrences(*path_parts, include_base=True, dir=False):
	path = os.path.join(*path_parts)
	occurrences = []
	path_check = os.path.isdir if dir else os.path.isfile
	
	for plugin in reversed(config.plugins.activated):
		plugin_path = os.path.join(plugin_base_path(plugin), path)
		if path_check(plugin_path):
			occurrences.insert(0, plugin_path)
	
	if include_base:
		base_instance_path = os.path.join(__home__, path)
		if path_check(base_instance_path):
			occurrences.insert(0, base_instance_path)

	return occurrences

@export
def get_path(*path_parts, include_base=True, is_dir=False):
	return get_path_occurrences(*path_parts, include_base=include_base, dir=is_dir)[0]
