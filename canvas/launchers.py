#	coding utf-8
'''
Command line invocation.
'''

import re
import os
import sys

from .namespace import export
from .utils import logger
from .core.plugins import plugin_base_path
from .core import initialize, serve
from . import __home__

_launchers = dict()

log = logger(__name__)

@export
def launcher(name, argspec):
	def launcher_wrap(func):
		func.__argspec__ = argspec
		_launchers[name] = func
		return func
	return launcher_wrap

@launcher('serve', '<port>')
def launch_serve(args):
	try:
		port = int(args[0])
	except:
		return False
	serve(port)
	return True

@launcher('create-plugin', '<name>')
def launch_creation(args):
	if len(args) != 1:
		return False
	
	plugin_name = args[0]
	plugin_dir = plugin_base_path(plugin_name)

	try:
		os.mkdir(plugin_dir)
	except OSError:
		log.critical('The plugin "%s" already exists, aborting'%plugin_name)
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
		'dependencies.txt',
		'requirements.txt',
		'settings.json'
	]
	for template in direct_copies:
		copy_template(template)

	copy_template('pkg.__init__.py', os.path.join(plugin_name, '__init__.py'))
	copy_template('tests.__init__.py', os.path.join('tests', '__init__.py'))

	log.info('Created plugin "%s" (in %s)'%(plugin_name, plugin_dir))
	return True

@export
def launch(launcher_param, *args):
	initialize()

	launcher_match = re.match(r'--(.*)', launcher_param)
	if launcher_match is None or launcher_match.group(1) not in _launchers:
		launch_options = ' '.join([
			'Usage:',
			'python canvas [\n',
				'\n'.join([
					'--%s %s'%(name, launcher.__argspec__) for name, launcher in _launchers.items()
				]),
			'\n]'
		])
		print(launch_options)
	else:
		launcher = _launchers[launcher_match.group(1)]
		if not launcher(args):
			print('Usage: --%s %s'%(launcher_param, launcher.__argspec__))
