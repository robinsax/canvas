#	coding utf-8
'''
Command line invocation.
'''

import re

from .namespace import export
from .core import serve

_launchers = dict()

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

@export
def launch(launcher_param, *args):
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
			print('Usage: --%s %s'%(launcher_name, launcher.__argspec__))
