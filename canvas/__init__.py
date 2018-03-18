#	coding utf-8
'''
canvas is a full-stack web application framework designed to make modern web
application development easier.

This is its back end interface and engine.
'''

__version__ = '0.2'

import os
import sys
import inspect

HOME = os.path.abspath(
	os.path.dirname(
		os.path.dirname(inspect.getfile(sys.modules[__name__]))
	)
)

from . import core, launchers, tests
