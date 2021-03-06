# coding: utf-8
'''
The plugin management system handles plugin loading and offers an interface for
filesystem access of plugin contents.
'''

import os
import re
import sys
import git
import traceback

from zipfile import ZipFile, ZIP_DEFLATED

from ..exceptions import DependencyError, Failed
from ..utils import logger
from ..configuration import config, add_importer_override
from ..json_io import serialize_json, deserialize_json
from .. import __home__

#	Create a logger.
log = logger(__name__)

#	Define a master list of the names of loaded plugins.
_loaded_plugins = list()

def plugin_base_path(name):
	'''
	Return the path to the root directory of the plugin whose package name is 
	`name`.
	'''
	name = name.split('.')[-1]
	return os.path.join(__home__, config.plugins.directory, 'cvpl-%s'%name)

def package_plugin(name, directory, dest_file):
	'''Package a plugin for repository deposit.'''
	if not dest_file.endswith('.cvpl'):
		dest_file = '.'.join((dest_file, 'cvpl'))
	log.info('Packaging plugin "%s": %s -> %s'%(name, directory, dest_file))

	#	Collect package metadata.
	try:
		repo = git.Repo(directory)
	except git.InvalidGitRepositoryError:
		raise Failed('Must be a git repository') from None
	repo_url = repo.remotes[0].url
	
	try:
		with open(os.path.join(directory, 'plugin.json')) as plugin_file:
			plugin_config = deserialize_json(plugin_file.read())
		dependencies = list(
			d[0] if isinstance(d, list) else d for d in plugin_config['dependencies']
		)
	except:
		raise Failed('Invalid plugin.json') from None

	meta_dir = os.path.join(directory, '.canvas')
	if not os.path.exists(meta_dir):
		os.mkdir(meta_dir)
	with open(os.path.join(meta_dir, 'meta.json'), 'w') as meta_file:
		meta_file.write(serialize_json({
			'repo_url': repo_url,
			'name': name,
			'description': input('Provide a short description: '),
			'dependencies': dependencies
		}))
	
	dirs_to_package = list(
		os.path.join(directory, d) for d in (
			name, '.canvas', 'assets', 'palettes', 'tests'
		)
	)
	#	Package.
	package = ZipFile(dest_file, 'w', compression=ZIP_DEFLATED)
	for root, dirs, files in os.walk(directory):
		if root != directory:
			should_package = False
			for dir_name in dirs_to_package:
				if dir_name in root:
					should_package = True
					break
			if not should_package:
				continue
		for item in files:
			package.write(
				os.path.join(root, item), 
				arcname=os.path.join(root[len(directory):], item)
			)
	
	log.info('Packaged to "%s"'%dest_file)

def load_plugins():
	'''Load all active plugins and their dependencies.'''
	#	Import the namespace into which the plugins will be imported.
	from .. import plugins as plugins_namespace

	#	Load a single plugin.
	def load_plugin(name, dependency_of=None):
		#	Decide the base and configuration paths for this plugin.
		path = plugin_base_path(name)
		config_path = os.path.join(path, 'plugin.json')

		if os.path.exists(config_path):
			#	Load the configuration if it exists.
			with open(config_path) as config_file:
				raw_plugin_config = deserialize_json(config_file.read())
				if 'dependencies' in raw_plugin_config:
					dependencies = raw_plugin_config['dependencies']
				else:
					dependencies = tuple()
			
			#	Load all depenencies imported by this plugin.
			for dependency in dependencies:
				if isinstance(dependency, (tuple, list)):
					dependency, importer_config = dependency
					add_importer_override(dependency, importer_config)
				load_plugin(dependency, name)

		#	Make the plugin importable.
		sys.path.insert(0, path)
		#	Log the import.
		plugin_label = name
		if dependency_of:
			plugin_label = '%s (from %s)'%(plugin_label, dependency_of)
		log.info('Loading plugin %s', plugin_label)
		
		try:
			#	Import the plugin as a member of the plugins namespace.
			plugins_namespace.__path__.append(path)
			__import__('canvas.plugins.%s'%name)
		except ModuleNotFoundError as ex:
			length = len(list(traceback.walk_tb(ex.__traceback__)))
			if length == 1:
				#	This occurred immediatly above.
				raise DependencyError('Plugin not found: %s'%plugin_label)
			#	This occurred within the plugin.
			raise ex
		
		#	Add the plugin to the master list.
		_loaded_plugins.append(name)

	#	Load each plugin activated in the base configuration.
	for plugin in config.plugins.activated:
		load_plugin(plugin)

def get_path_occurrences(*path_parts, include_base=True, is_dir=False):
	'''
	Return all occurrences of the path with fragements `path_parts` in all 
	loaded plugins (and optionally canvas itself) that either are or aren't a 
	directory.
	'''
	path, occurrences = os.path.join(*path_parts), list()
	#	Resolve the path inspection callable.
	path_check = os.path.isdir if is_dir else os.path.isfile
	
	#	Iterate all loaded plugins.
	for plugin in reversed(_loaded_plugins):
		plugin_path = os.path.join(plugin_base_path(plugin), path)
		if path_check(plugin_path):
			occurrences.insert(0, plugin_path)
	
	if include_base:
		#	Check for and maybe include a base instance.
		base_instance_path = os.path.join(__home__, path)
		if path_check(base_instance_path):
			occurrences.insert(0, base_instance_path)

	return occurrences

def get_path(*path_parts, include_base=True, is_dir=False):
	'''
	Return the first instance returned by `get_path_occurances` or `None`.
	'''
	occurrences = get_path_occurrences(*path_parts, include_base=include_base, 
			is_dir=is_dir)
	return occurrences[-1] if occurrences else None
