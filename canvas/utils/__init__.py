#	coding utf-8
'''
The canvas utilities package
'''

import json
import inspect
import logging
import traceback as tb

from .registration import *

#	Imported to package level
__all__ = [
	'make_json',
	'format_traceback',
	'export_to_module',
	'copy_dict',
	'logger',
	'register',
	'get_registered',
	'get_registered_by_name',
	'call_registered',
	'place_registered_on',
	'WrappedDict'
]

class WrappedDict(dict):
	'''
	A dictionary subclass for `KeyError` replacement.
	'''

	def __init__(self, content, ex_cls):
		'''
		:content The content to set
		:ex_cls The exception class to raise instead
			of `KeyError`
		'''
		self.ex_cls = ex_cls
		for k, v in content.items():
			self[k] = v

	def __getitem__(self, key):
		if key not in self:
			raise self.ex_cls(key)
		return super().__getitem__(key)

# TODO: Bounce to core?
def make_json(status_str, *data_dict, status=200, headers={}, default=None):
	'''
	:status The status as a string. Should be one
		of: `'success'`, `'failure'`, or `'error'`
	:data_dict (Optional) A data package
	'''
	if len(data_dict) > 0:
		return json.dumps({
			'status': status_str,
			'data': data_dict[0]
		}, default=default), status, headers, 'application/json'
	else:
		return json.dumps({
			'status': status_str
		}, default=default), status, headers, 'application/json'

def format_traceback(error):
	'''
	Return a traceback in string format
	:error An error that was at some point raised 
	'''
	traceback = (''.join(tb.format_tb(error.__traceback__))).strip().replace('\n    ', '\n\t').replace('\n  ', '\n')
	return f'{error.__class__.__name__}: {error}\n{traceback}'

def logger():
	'''
	Alias for `logging.getLogger()`. Must be invoked 
	at module level
	'''
	name = inspect.stack()[-1].frame.f_locals.get('__name__', '<local>')
	return logging.getLogger(name)

def copy_dict(o_dict, *keys):
	n_dict = {}
	for key in keys:
		n_dict[key] = o_dict[key]
	return n_dict

def export_to_module(module, *items, into_all=True):
	'''
	Export something onto a module.
	'''
	if into_all:
		if not hasattr(module, '__all__'):
			module.__all__ = []
		module.__all__.extend(items)
	for item in items:
		setattr(module, item.__name__.split('.')[-1], item)
