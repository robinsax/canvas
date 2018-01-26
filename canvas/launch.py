#	coding utf-8
'''
Command line launch handler interface and default implementations.
'''

import sys

from .utils.registration import register
from .utils import logger

#	Declare exports.
__all__ = [
	'LaunchMode',
	'DevServeMode',
	'UnitTestMode',
	'BuildDocsMode',
	'CreatePluginMode'
]

log = logger()

class LaunchMode:
	'''
	`LaunchMode`s handle command-line invocation of canvas for a specific mode.
	The mode is prefixed with `--` in the command line.

	Implementations' constructors must take no parameters.
	'''

	def __init__(self, mode, arg_fmt=''):
		'''
		Create a new launch handler. Must be registered as `launch_mode` for 
		actuation.
		
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
	The development serving mode, invoked with `--serve`.
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
	The unit test execution mode, invoked with `--run_tests`.
	'''

	def __init__(self):
		super().__init__('run_tests', '<suite_1> ... <suite_n>')

	def launch(self, args):
		from .tests import run_tests

		if not run_tests(args):
			sys.exit(1)
		return True

@register.launch_mode
class BuildDocsMode(LaunchMode):
	'''
	The code documentation generation mode, invoked with `--build_docs`.
	'''
	def __init__(self):
		super().__init__('build_docs', '[<target_plugin>]')

	def launch(self, args):
		import canvas

		from .utils.doc_builder import build_docs

		if len(args) > 0:
			try:
				package = sys.modules[args[0]]
			except:
				return False
		else:
			package = canvas

		build_docs(package)
		log.info('Docs built')
		return True

@register.launch_mode
class CreatePluginMode(LaunchMode):
	'''
	The plugin template generation mode, invoked with `--create_plugin`
	'''

	def __init__(self):
		super().__init__('create_plugin', '<plugin_name>')

	def launch(self, args):
		from .utils.plugin_generator import create_plugin_template

		try:
			plugin_name = args[0]
		except:
			return False

		create_plugin_template(plugin_name)
		log.info('Plugin created')
		return True

@register.launch_mode
class ActivatePluginMode(LaunchMode):
	'''
	The plugin activation mode. Mostly a development helper. Invoked with 
	`--activate_plugin`.
	'''

	def __init__(self):
		super().__init__('activate_plugin', '<plugin_name>')

	def launch(self, args):
		from . import config
		from .configuration import write

		try:
			plugin_name = args[0]
		except:
			return False
		if plugin_name not in config['plugins']['active']:
			config['plugins']['active'].append(plugin_name)

		write(config)
		log.info(f'Activated plugin {plugin_name}')
		return True
