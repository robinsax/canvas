#	coding utf-8
'''
Canvas plugin management
'''

import os
import sys
import logging

from ..exceptions import PluginInitError
from ..utils import logger
from .. import CANVAS_HOME, config

log = logger()

class CanvasPluginLoader:

	def __init__(self, module):
		self.module = module

	def load_module(self, module_name):
		return self.module

class CanvasPluginImporter:

	def __init__(self, modules):
		self.modules = modules
	
	def load_module(self, module_name):
		return self

	def find_module(self, module_name, package_path):
		if module_name == 'canvas.plugins':
			return self
		return CanvasPluginLoader(self.modules[module_name])

def plugin_base_path(name):
	return os.path.join(config['plugins']['directory'], f'canvas-pl-{name}')

def load_all():
	'''
	Load all activated plugins
	'''
	loaded = {}
	for plugin in config['plugins']['active']:
		sys.path.insert(0, plugin_base_path(plugin))
		log.debug(f'Importing plugin {plugin}')
		try:
			__import__(plugin)
			loaded[plugin] = sys.modules[plugin]
		except BaseException as e:
			raise PluginInitError(plugin)
	
	#	Create an alternate import loader
	#	that allows canvas.plugins.X imports
	sys.meta_path.append(CanvasPluginImporter(loaded))

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
		#	Check this base since it has lowest priority
		base_instance_path = os.path.join(CANVAS_HOME, 'canvas', target)
		if filter(base_instance_path):
			occurrences.insert(0, base_instance_path)

	return occurrences
