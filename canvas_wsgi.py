#	coding utf-8
'''
The WSGI application to be passed to the WSGI
server.

Canonically should be a .wsgi file, but wfastcgi.py 
is picky about file extension, and Apache doesn't 
seem to care, so `.py` is used to support IIS.
'''

from canvas import application
