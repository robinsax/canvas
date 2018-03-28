#	coding utf-8
'''
canvas is a full-stack web application framework designed to make modern web
application development easier.
'''

__version__ = '0.2'

import os
import sys
import inspect

__home__ = os.path.abspath(
	os.path.dirname(
		os.path.dirname(inspect.getfile(sys.modules[__name__]))
	)
)

try:
	#	These imports will fail if dependencies haven't been installed.
	from . import core, tests, plugins
except ImportError: pass

from . import launchers
