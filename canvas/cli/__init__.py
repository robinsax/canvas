# coding: utf-8
'''
Command line interface API and default launch mode implementations. CLI 
invocation in canvas causes a lookup against registered launchers, which
plugins are welcome to provide via the `launcher` function decorator.
'''

import re
import sys

from .. import __home__, __version__
from .api import launcher, launch_cli

#	The following imports are not exposed; they are just being initialized.
from . import plugin_creation, setup

@launcher('version',
	description='Show the current version'
)
def show_version(args):
	print('canvas %s'%__version__)
	return True

@launcher('serve',
	argspec='<port>', 
	description='Launch the development server', 
	init=True
)
def launch_serve(args):
	from ..core import serve

	try:
		port = int(args[0])
	except:
		return False
	
	serve(port)
	return True

@launcher('test',
	argspec='<?plugin>',
	description='Run unit tests on the core or a plugin',
	init=True
)
def launch_tests(args):
	from ..core.plugins import plugin_base_path

	if len(args) > 0:
		import_from = plugin_base_path(args[0])
	else:
		import_from = __home__

	sys.path.insert(0, import_from)
	import tests
	
	if not run_tests():
		sys.exit(1)
	return True
