#	coding utf-8
'''
Command line launch handler interface and 
default implementations.
'''

import sys

from werkzeug.serving import run_simple

from .utils.registration import register
from .tests import run_tests

__all__ = [
	'LaunchMode',
	'DevServeMode',
	'UnitTestMode'
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
	
	def handle(self, args):
		'''
		Handle a command line invocation. Return `True` if the
		command line input was valid and `False` otherwise.

		If `False` is returned, the argument specification is
		presented.

		:args The command line arguments
		'''
		raise NotImplemented()

@register('launch_mode')
class DevServeMode(LaunchMode):
	'''
	The development serving mode, triggered by `--serve`.
	'''

	def __init__(self):
		super().__init__('serve', 'PORT')

	def handle(self, args):
		from canvas import application

		#	Parse arguments.
		try:
			port = int(args[0])
		except:
			return False
		
		run_simple('localhost', port, application)
		return True

@register('launch_mode')
class UnitTestMode(LaunchMode):
	'''
	The unit test execution mode, triggered by `--run_tests`.
	'''

	def __init__(self):
		super().__init__('run_tests', 'SUITE_1 ... SUITE_N')

	def handle(self, args):
		if not run_tests(args):
			sys.exit(1)
		return True
