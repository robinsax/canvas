#	coding utf-8
'''
Plugin generation.
'''

import os
import sys

from ..utils import logger
from .. import __home__
from . import launcher

log = logger(__name__)

@launcher('create-plugin',
	argspec='<name>', 
	description='Create a plugin template', 
	init=True
)
def launch_plugin_creation(args):
	from ..core.plugins import plugin_base_path

	if len(args) != 1:
		return False
	
	plugin_name = args[0]
	plugin_dir = plugin_base_path(plugin_name)

	try:
		os.mkdir(plugin_dir)
	except OSError:
		log.critical('The plugin "%s" already exists (aborting)'%plugin_name)
		sys.exit(1)
	
	os.mkdir(os.path.join(plugin_dir, plugin_name))
	os.mkdir(os.path.join(plugin_dir, 'tests'))
	os.mkdir(os.path.join(plugin_dir, 'assets'))

	def copy_template(src_filename, dest_filename=None):
		if not dest_filename:
			dest_filename = src_filename

		src_path = os.path.join(__home__, 'etc', 'plugin_templates', src_filename)
		with open(src_path, 'r') as src_file:
			src = src_file.read()
		
		src = src.replace('$plugin_name', plugin_name)

		with open(os.path.join(plugin_dir, dest_filename), 'w') as dest_file:
			dest_file.write(src)

	direct_copies = [
		'.coveragerc',
		'.gitignore',
		'.travis.yml',
		'requirements.txt',
		'plugin.json'
	]
	for template in direct_copies:
		copy_template(template)

	copy_template('pkg.__init__.py', os.path.join(plugin_name, '__init__.py'))
	copy_template('tests.__init__.py', os.path.join('tests', '__init__.py'))

	log.info('Created plugin "%s" (in %s)'%(plugin_name, plugin_dir))
	return True
