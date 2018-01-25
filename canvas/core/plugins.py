#	coding utf-8
'''
Plugin management. Packaged within core to allow
an empty `canvas.plugins` namespace for population.
'''

import os
import sys
import logging

from ..utils import logger
from .. import CANVAS_HOME, config

log = logger()

def plugin_base_path(name):
	'''
	Return the path to the root directory of the 
	plugin named `name`.

	:name The name of the plugin.
	'''
	return os.path.join(CANVAS_HOME, config['plugins']['directory'], f'canvas-pl-{name}')

def load_all_plugins():
	'''
	Initialize all plugins activated in configuration
	and populate the `canvas.plugins` namespace.
	'''
	loaded = []
	for plugin in config['plugins']['active']:
		path = plugin_base_path(plugin)

		#	Add to path to allow import.
		sys.path.insert(0, path)

		#	Import.
		log.debug(f'Importing plugin {plugin}')
		__import__(plugin)
		loaded.append(path)
	
	#	Populate the canvas.plugins namespace
	from .. import plugins as plugins_namespace
	plugins_namespace.__path__.extend(loaded)

def get_path_occurrences(target, include_base=True, filter=os.path.exists):
	'''
	Return a list of absolute paths to all files or directories
	with the given name in activated plugin directories, in order
	of __ascending priority__.

	Priority is determined as plugin occurrences by 
	activiation order *then* base occurrence.
	
	:target The search target as a relative path
	:filter An additional filter on inclusion given `path`, the
		absolute path to the file or folder
	:include_base Whether to also add the instance from the base
		canvas package, if it exists
	'''
	occurrences = []
	
	for plugin in reversed(config['plugins']['active']):
		#	Check plugins in reverse order so
		#	the first loaded would go on last,
		#	etc.
		path = os.path.join(plugin_base_path(plugin), target)
		if filter(path):
			occurrences.insert(0, path)

	if include_base:
		#	Check this base instance last since it has 
		#	lowest priority
		base_instance_path = os.path.join(CANVAS_HOME, 'canvas', target)
		if filter(base_instance_path):
			occurrences.insert(0, base_instance_path)

	return occurrences
