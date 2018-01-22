#	coding utf-8
'''
Utilities for the canvas core and plugins.
'''

import json
import inspect
import logging
import traceback as tb

#	Import subpackage to namespace.
from .registration import *
from .template_utils import *

#	Declare exports.
__all__ = [
	#	Functions.
	'format_traceback',
	'export_to_module',
	'logger',
	#	Subpackage functions - registration.
	'register',
	'callback',
	'get_registered',
	'get_registered_by_name',
	'call_registered',
	'place_registered_on',
	#	Subpackage functions - template_utils.
	'markup',
	'markdown',
	'uri_encode',
	'json',
	#	Classes.
	'WrappedDict'
]

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
	return logging.getLogger(name)

def export_to_module(module, *items, into_all=True):
	'''
	Export one or more functions or classes onto a module.

	:module The target module object
	:items The functions or classes to place.
	:into_all Whether to add the functions or objects
		to the `__all__` list of the target module.
	'''
	if into_all:
		#	Add to the `__all__` list of target.
		if not hasattr(module, '__all__'):
			#	Create the all object if it doesn't exist.
			module.__all__ = []
		module.__all__.extend(items)
	
	for item in items:
		#	Place the object in the modules namespace.
		setattr(module, item.__name__.split('.')[-1], item)
