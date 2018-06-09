#	coding utf-8
'''
canvas is a full-stack web application framework for building API-driven,
reactive web applications.
'''

#	Define the version.
__version__ = '0.3'

import os
import sys
import inspect

#	Locate the current directory.
__home__ = os.path.abspath(
	os.path.dirname(
		os.path.dirname(inspect.getfile(sys.modules[__name__]))
	)
)
#	Define the supported verb set.
__verbs__ = ['get', 'post', 'put', 'patch', 'delete', 'options']

#	Check whether requirements have been installed.
__installed__ = True
try:
	import werkzeug, psycopg2
except ImportError:
	__installed__ = False

if __installed__:
	#	Fully initialize canvas.
	from . import core, tests, plugins
#	Initialize the loader API for launch.
from . import launchers
