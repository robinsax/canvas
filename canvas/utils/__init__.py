#	coding utf-8
'''
Utilities for the canvas core and plugins.
'''

import time
import inspect
import logging
import traceback as tb

from werkzeug.serving import run_simple

#	Import subpackage to namespace.
from .registration import *
from .json_serializers import *
from .uploads import *
from .template_utils import *

#	Declare exports.
__all__ = [
	#	Functions.
	'serve',
	'format_traceback',
	'logger',
	'current_time',
	#	Subpackage functions - registration.
	'register',
	'callback',
	'get_registered',
	'get_registered_by_name',
	'clear_registered',
	'call_registered',
	'place_registered_on',
	#	Subpackage functions - template_utils.
	'markup',
	'markdown',
	'uri_encode',
	'json',
	#	Subpackage functions - json_serializers.
	'JSONSerializer',
	'serialize_json',
	'deserialize_json',
	#	Classes.
	'WrappedDict'
]

def serve(port):
	'''
	Serve the canvas development server on `localhost`.
	
	Cannot be called until canvas is initialized.
	'''
	from .. import application

	run_simple('0.0.0.0', port, application)

class WrappedDict(dict):
	'''
	A dictionary with a configurable key error.
	'''

	def __init__(self, source, exception_cls):
		'''
		Copy the dictionary `source` into this dictionary
		and define the exception class to replace `KeyError`.

		:source The dictionary to copy into this
			dictionary.
		:exception_cls The exception class to raise when
			a missing key is retrieve. Instances will have the
			offending key passed to their constructor.
		'''
		#	Copy source into self.
		for k, v in source.items():
			self[k] = v

		#	Save the exception class.
		self.exception_cls = exception_cls

	def __getitem__(self, key):
		'''
		Retrieve the value for `key` or raise
		an exception if it's not present.
		'''
		if key not in self:
			#	Key error.
			raise self.exception_cls(key)

		#	Return the value.
		return super().__getitem__(key)

	def pop(self, key):
		value = self[key]
		del self[key]
		return value

def format_traceback(error):
	'''
	Return a formatted traceback string for `error` if it has
	been raised.

	:error The raised error.
	'''
	traceback = (''.join(tb.format_tb(error.__traceback__))).strip().replace('\n    ', '\n\t').replace('\n  ', '\n')
	return f'{error.__class__.__name__}: {error}\n{traceback}'

def logger(name=None):
	'''
	Create and return a standard library `logging.Logger`.
	When invoked at package level, the name parameter can
	be safely omitted.

	:name The name of the logger to create.
	'''
	if name is None:
		#	Guess name.
		#	TODO: Not working in some places
		name = inspect.stack()[-1].frame.f_locals.get('__name__', '<local>')
	
	#	Create and return logger.
	log = logging.getLogger(name)
	return log

def current_time():
	'''
	Return the current time in milliseconds.
	'''
	return int(time.time()*1000)
