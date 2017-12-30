#	coding utf-8
'''
Canvas plugin management
'''

import os
import sys
import logging

from ..exceptions import PluginInitError
from .. import CANVAS_HOME, config

log = logging.getLogger(__name__)

def load_all():
	'''
	Load all activated plugins
	'''
	plugin_dir = config['plugins']['directory']
	for plugin in config['plugins']['active']:
		sys.path.insert(0, os.path.join(plugin_dir, plugin))
		log.debug(f'Importing plugin {plugin}')
		try:
			__import__(plugin)
		except BaseException as e:
			raise PluginInitError(plugin)

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

	if include_base:
		#	Check this base since it has lowest priority
		base_instance_path = os.path.join(CANVAS_HOME, 'canvas', target)
		if filter(base_instance_path):
			occurrences.append(base_instance_path)
	
	for plugin in reversed(config['plugins']['active']):
		#	Check plugins in reverse order so
		#	the first loaded would go on last,
		#	etc.
		path = os.path.join(config['plugins']['directory'], plugin, target)
		if filter(path):
			occurrences.append(path)

	return occurrences
