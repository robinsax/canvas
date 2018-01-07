#	coding utf-8
'''
Canonically should be a .wsgi file, but I've noticed
wfastcgi.py is picky about file extension, and Apache
doesn't seem to care, so I've used .py to support IIS
'''

import os
from sys import path

CANVAS_HOME = 'CANVAS_HOME'
if CANVAS_HOME not in os.environ:
	os.environ[CANVAS_HOME] = '/var/www/canvas'
path.insert(0, os.environ['CANVAS_HOME'])

from canvas import application