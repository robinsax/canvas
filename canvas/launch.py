#	coding utf-8
'''
The command-line invocation handler interface and default implementations.
'''

import os
import sys
import shutil

from .configuration import (
	write as write_configuration,
	load as load_configuration
)
from .exceptions import NoSuchPlugin
from .utils.registration import register
from .utils.doc_builder import build_docs
from .utils import logger, serve
from .core.plugins import plugin_base_path
from . import CANVAS_HOME, config

#	Declare exports.
__all__ = [
	'LaunchMode'
]

#	Declare the template directory path.
TEMPLATE_DIR = os.path.join(CANVAS_HOME, './etc/templates')

#	Create a logger.
log = logger(__name__)

class LaunchMode:
	'''
	`LaunchMode`s handle command-line invocation of canvas in a specific mode.
	The mode is specified as the first arguments, prefixed with `--`, provided
	in the command-line.

	To be actualized, `LaunchMode`s must be registered as `launch_mode` using
	the registration decorator.
	'''

	def __init__(self, mode, arg_fmt=''):
		'''
		Create a launch handler.
		
		:mode The mode string (e.g. `serve` to be triggered by `--serve`).
		:arg_fmt The usage format (i.e. argument specification), as a string.
		'''
		self.mode, self.arg_fmt = (mode, arg_fmt)
	
	def launch(self, args):
		'''
		Handle a command line invocation. Return `True` if the command line 
		input was valid and `False` otherwise.

		If `False` is returned, the argument specification is presented.

		:args The command line arguments.
		'''
		raise NotImplemented()

@register.launch_mode
class DevServeMode(LaunchMode):
	'''
	The development server initializer.
	'''

	def __init__(self):
		super().__init__('serve', '<port>')

	def launch(self, args):
		from .utils import serve

		#	Parse arguments.
		try:
			port = int(args[0])
		except:
			return False
		
		serve(port)
		return True

@register.launch_mode
class UnitTestMode(LaunchMode):
	'''
	The unit test execution mode.
	'''

	def __init__(self):
		super().__init__('run-tests', '<suite_1> ... <suite_n>')

	def launch(self, args):
		from .tests import run_tests

		#	Run the tests, exiting with a non-zero code if they fail, to inform
		#	CI tools.
		if not run_tests(args):
			sys.exit(1)
		return True

@register.launch_mode
class BuildDocsMode(LaunchMode):
	'''
	The code documentation generation mode.
	'''
	def __init__(self):
		super().__init__('build-docs', '[<target_plugin>]')

	def launch(self, args):
		if len(args) > 0:
			try:
				package = sys.modules[args[0]]
			except:
				return False
		else:
			#	Run core tests by default.
			import canvas
			package = canvas

		build_docs(package)
		log.info('Documentation built')
		return True

@register.launch_mode
class CreatePluginMode(LaunchMode):
	'''
	The plugin template generation mode.
	'''

	def __init__(self):
		super().__init__('create-plugin', '<plugin_name>')

	def launch(self, args):
		try:
			name = args[0]
		except:
			return False

		#	Load target directory from configuration or fail.
		target_dir = os.path.join(CANVAS_HOME, config['plugins']['directory'])
		
		def detemplate_file_to(src, dest):
			'''
			Load and detemplate `src`, then write to `dest`
			'''
			with open(src, 'r') as src_f, open(dest, 'w') as dest_f:
				dest_f.write(src_f.read().replace(f'$plugin_name', name))

		#	Create the root directory
		root = f'{target_dir}/canvas-pl-{name}'
		os.makedirs(root)
		#	...and package.
		pkg_root = f'{root}/{name}'
		os.mkdir(pkg_root)
		test_root = f'{root}/tests'
		os.mkdir(test_root)

		#   Copy templates.
		detemplate_file_to(f'{TEMPLATE_DIR}/plugin/settings.json', f'{root}/settings.json')
		detemplate_file_to(f'{TEMPLATE_DIR}/plugin/.travis.yml', f'{root}/.travis.yml')
		detemplate_file_to(f'{TEMPLATE_DIR}/plugin/pkg.__init__.py', f'{pkg_root}/__init__.py')
		detemplate_file_to(f'{TEMPLATE_DIR}/plugin/tests.__init__.py', f'{test_root}/__init__.py')

		#	Copy non-template.
		shutil.copyfile(f'{TEMPLATE_DIR}/plugin/.gitignore', f'{root}/.gitignore')
		shutil.copyfile(f'{TEMPLATE_DIR}/plugin/dependencies.txt', f'{root}/dependencies.txt')
		shutil.copyfile(f'{TEMPLATE_DIR}/plugin/requirements.txt', f'{root}/requirements.txt')
		shutil.copyfile(f'{TEMPLATE_DIR}/plugin/.coveragerc', f'{root}/.coveragerc')

		#	Create assets folder.
		os.mkdir(f'{root}/assets')
		#	Create documentation folder.
		os.mkdir(f'{root}/docs')
		os.mkdir(f'{root}/docs/code')

		log.info(f'Created plugin {name} in {root}')
		return True

@register.launch_mode
class ActivatePluginMode(LaunchMode):
	'''
	The plugin activation list configuration mode.
	'''

	def __init__(self):
		super().__init__('use-plugins', '<set|add|remove> <plugin_1>, ..., <plugin_n>')

	def launch(self, args):
		#	Assert input is valid.
		try:
			operation, *plugins = args
		except:
			return False
		if operation not in ['add', 'set', 'remove']:
			return False
		
		new_list, prev_list = [], config['plugins']['active']
		if operation == 'set':
			to_load = plugins
		elif operation == 'add':
			to_load = plugins + prev_list
		elif operation == 'remove':
			to_load = [name for name in prev_list if name not in plugins]

		def activate_one(name, source=None):
			if name in new_list:
				return
			reference = name if source is None else f'{name} (from {source})'
			log.info(f'Activating plugin {reference}')
			
			path = plugin_base_path(name)

			#	Assert this plugin exists.
			if not os.path.exists(path):
				raise NoSuchPlugin(reference)
			
			#	Load dependencies, if they exist.
			dependencies_path = os.path.join(path, 'dependencies.txt')
			if os.path.exists(dependencies_path):
				with open(dependencies_path, 'r') as f:
					this_dependencies = [l.strip() for l in f.readlines() if len(l.strip()) > 0]
				for dependency in this_dependencies:
					activate_one(dependency, name)
			
			#	Add
			new_list.append(name)

		for name in to_load:
			activate_one(name)

		new_config = load_configuration(configure_logger=False)
		new_config['plugins']['active'] = new_list
		write_configuration(new_config)

		log.info(f'Activated plugins: {", ".join(new_list)}')
		return True

@register.launch_mode
class SetPluginDirMode(LaunchMode):

	def __init__(self):
		super().__init__('set-plugin-dir', '<dirpath, relative to canvas>')

	def launch(self, args):
		#	Assert input is valid.
		try:
			path = args[0]
		except:
			return False

		if not os.path.exists(os.path.join(CANVAS_HOME, path)):
			log.critical(f'No such directory {path}')
			return True

		new_config = load_configuration(configure_logger=False)
		new_config['plugins']['directory'] = path
		write_configuration(new_config)
		
		log.info(f'Set plugin directory: {path}')
		return True
