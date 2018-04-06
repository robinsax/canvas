#	coding utf-8
'''
Command line invocation.
'''

import re
import sys

from ..namespace import export
from ..tests import run_tests
from .. import __home__, __version__

_launchers = dict()

@export
def launcher(name, info):
	def launcher_wrap(func):
		func.__info__ = info
		_launchers[name] = func
		return func
	return launcher_wrap

@launcher('version', {
	'description': 'Show the current version'
})
def show_version(args):
	print('canvas %s'%__version__)
	return True

@launcher('serve', {
	'argspec': '<port>', 
	'description': 'Launch the development server', 
	'init': True
})
def launch_serve(args):
	from ..core import serve

	try:
		port = int(args[0])
	except:
		return False
	
	serve(port)
	return True

@launcher('test', {
	'argspec': '<?plugin>',
	'description': 'Run unit tests on the core or a plugin',
	'init': True
})
def launch_tests(args):
	from ..core.plugins import plugin_base_path

	if len(args) > 0:
		import_from = plugin_base_path(args[0])
	else:
		import_from = __home__

	sys.path.insert(0, import_from)
	import tests
	
	run_tests()
	return True

@export
def launch(args):
	def print_usage():
		def create_string(name, launcher):
			first = '--%s %s'%(name, launcher.__info__.get('argspec', ''))
			first = '%s%s%s'%(first, ' '*(30 - len(first)), launcher.__info__.get('description', ''))
			return first

		print(' '.join([
			'Usage:',
			'python canvas [',
				'\n\t' + '\n\t'.join([
					create_string(name, launcher) for name, launcher in _launchers.items()
				]),
			'\n]'
		]))
		sys.exit(1)

	def get_launcher(item):
		launcher_match = re.match(r'--(.*)', args[k])
		if launcher_match is None:
			return None
		return launcher_match.group(1) 

	k = 0
	launcher = None
	while k < len(args):
		launcher = get_launcher(args[k])
		if launcher is None or launcher not in _launchers:
			print_usage()
		k += 1

		args_here = []
		while k < len(args) and get_launcher(args[k]) is None:
			args_here.append(args[k])
			k += 1

		launcher = _launchers[launcher]
		if launcher.__info__.get('init', False):
			from ..core import initialize
			initialize()

		if not launcher(args_here):
			print_usage()

from . import plugin_creation, setup
