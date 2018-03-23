#	coding utf-8
'''
Plugin management.
'''

import os
import re
import sys

from ..exceptions import DependencyError
from ..namespace import export
from ..utils import logger
from ..configuration import config
from .. import __home__

log = logger(__name__)

def plugin_base_path(name):
	name = name.split('.')[-1]
	return os.path.join(__home__, config.plugins.directory, 'canvas-pl-%s'%name)

def load_plugins():
	from .. import plugins as plugins_namespace

	def load_plugin(name, dependency_of=None):
		path = plugin_base_path(name)
		dependency_path = os.path.join(path, 'dependencies.txt')

		if os.path.exists(dependency_path):
			with open(dependency_path) as dependency_file:
				dependencies = [l.strip() for l in dependency_file.readlines()]
			
			for dependency in dependencies:
				load_plugin(dependency, name)

		sys.path.insert(0, path)

		plugin_label = name
		if dependency_of:
			plugin_label = '%s (from %s)'%(plugin_label, dependency_of)
		log.info('Loading plugin: %s', plugin_label)
		try:
			plugins_namespace.__path__.append(path)
			__import__('canvas.plugins.%s'%name)
		except ModuleNotFoundError:
			raise DependencyError('Plugin not found: %s'%plugin_label) from None

	for plugin in config.plugins.activated:
		load_plugin(plugin)
		

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
		base_instance_path = os.path.join(__home__, 'canvas', path)
		if path_check(base_instance_path):
			occurrences.insert(0, base_instance_path)

	return occurrences
