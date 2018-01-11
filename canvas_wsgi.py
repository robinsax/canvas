#	coding utf-8
'''
Canonically should be a .wsgi file, but I've noticed
wfastcgi.py is picky about file extension, and Apache
doesn't seem to care, so I've used .py to support IIS
'''

import os
from sys import path

from canvas import application
