#	coding utf-8
'''
Command line invocation.
'''

import re

from ..namespace import export
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

@export
def launch(launcher_param, *args):
	launcher_match = re.match(r'--(.*)', launcher_param)

	def create_string(name, launcher):
		first = '--%s %s'%(name, launcher.__info__.get('argspec', ''))
		first = '%s%s%s'%(first, ' '*(30 - len(first)), launcher.__info__.get('description', ''))
		return first

	if launcher_match is None or launcher_match.group(1) not in _launchers:
		launch_options = ' '.join([
			'Usage:',
			'python canvas [',
				'\n\t' + '\n\t'.join([
					create_string(name, launcher) for name, launcher in _launchers.items()
				]),
			'\n]'
		])
		print(launch_options)
	else:
		launcher = _launchers[launcher_match.group(1)]
		if launcher.__info__.get('init', False):
			from ..core import initialize
			initialize()

		if not launcher(args):
			print('Usage: %s %s'%(launcher_param, launcher.__info__.get('argspec', '')))

from . import plugin_creation, setup
