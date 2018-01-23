#	coding utf-8
'''
Command line launch handler interface and 
default implementations.
'''

import sys

from .utils.registration import register

__all__ = [
	'LaunchMode',
	'DevServeMode',
	'UnitTestMode',
	'BuildDocsMode'
]

class LaunchMode:
	'''
	`LaunchMode`s handle command-line
	invocation of canvas for a specific mode.
	The mode is prefixed with `--` in the command line.

	Implementations' constructors must take no
	parameters.
	'''

	def __init__(self, mode, arg_fmt=''):
		'''
		Create a new launch handler. Must be
		registered as `launch_mode` for actuation.
		:mode The mode string (e.g. `serve` to be triggered
			by `--serve`).
		:arg_fmt The usage format (i.e. argument specification),
			as a string
		'''
		self.mode, self.arg_fmt = (mode, arg_fmt)
	
	def launch(self, args):
		'''
		Handle a command line invocation. Return `True` if the
		command line input was valid and `False` otherwise.

		If `False` is returned, the argument specification is
		presented.

		:args The command line arguments
		'''
		raise NotImplemented()

@register.launch_mode
class DevServeMode(LaunchMode):
	'''
	The development serving mode, invoked with `--serve`.
	'''

	def __init__(self):
		super().__init__('serve', 'PORT')

	def launch(self, args):
		from werkzeug.serving import run_simple
		from canvas import application

		#	Parse arguments.
		try:
			port = int(args[0])
		except:
			return False
		
		run_simple('localhost', port, application)
		return True

@register.launch_mode
class UnitTestMode(LaunchMode):
	'''
	The unit test execution mode, invoked with `--run_tests`.
	'''

	def __init__(self):
		super().__init__('run_tests', 'SUITE_1 ... SUITE_N')

	def launch(self, args):
		from .tests import run_tests

		if not run_tests(args):
			sys.exit(1)
		return True

@register.launch_mode
class BuildDocsMode(LaunchMode):
	'''
	The code documentation generation mode, invoked with '--build_docs'.
	'''
	def __init__(self):
		super().__init__('build_docs')

	def launch(self, args):
		from .build_docs import build_docs

		if not build_docs():
			sys.exit(1)
		return True
