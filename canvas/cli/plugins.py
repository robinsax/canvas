# coding: utf-8
'''
The plugin creation launcher which creates a new plugin from the templates 
found in `./etc/plugin_templates`.
'''

import os
import sys

from ..utils import logger
from .. import __home__
from .api import launcher

#	Create a logger.
log = logger(__name__)

@launcher('package-plugin', 
	argspec='<name> <destfile>',
	description='Package a plugin for upload',
	init=True
)
def launch_package_plugin(args):
	from ..core.plugins import plugin_base_path, package_plugin

	if len(args) != 2:
		return False
	plugin_name, dest_file = args
	plugin_dir = plugin_base_path(plugin_name)
	if not os.path.isdir(plugin_dir):
		print('No plugin "%s" to package'%plugin_name)
		return False

	package_plugin(plugin_name, plugin_dir, dest_file)
	return True

@launcher('make-plugin',
	argspec='<name>', 
	description='Create a new plugin', 
	init=True
)
def launch_plugin_creation(args):
	'''Create a new plugin from the template files.'''
	from ..core import plugin_base_path

	#	Assert usage is correct.
	if len(args) != 1:
		return False
	#	Decide plugin name and directory.
	plugin_name = args[0]
	plugin_dir = plugin_base_path(plugin_name)
	
	#	Create and asset that no such plugin exists already.
	try:
		os.mkdir(plugin_dir)
	except OSError:
		log.critical('The plugin "%s" already exists, aborting'%plugin_name)
		sys.exit(1)
	#	Create sub-directories.
	os.mkdir(os.path.join(plugin_dir, plugin_name))
	os.mkdir(os.path.join(plugin_dir, 'tests'))
	os.mkdir(os.path.join(plugin_dir, 'assets'))

	#	Define a template actualization helper.
	def copy_template(src_filename, dest_filename=None):
		#	Resolve arguments.
		if not dest_filename:
			dest_filename = src_filename
		src_path = os.path.join(
			__home__, 'etc', 'plugin_templates', src_filename
		)
		#	Read source file.
		with open(src_path, 'r') as src_file:
			src = src_file.read()
		
		#	Write the detemplated result to the destination file.
		with open(os.path.join(plugin_dir, dest_filename), 'w') as dest_file:
			dest_file.write(src.replace('$plugin_name', plugin_name))

	#	Directly copy most files.
	direct_copies = ('.coveragerc', '.gitignore', '.travis.yml', 
			'requirements.txt', 'plugin.json')
	
	for template in direct_copies:
		copy_template(template)
	#	Appropriately copy package root modules.
	copy_template('pkg.__init__.py', os.path.join(plugin_name, '__init__.py'))
	copy_template('tests.__init__.py', os.path.join('tests', '__init__.py'))
	
	log.info('Created plugin "%s" (in %s)'%(plugin_name, plugin_dir))
	return True
