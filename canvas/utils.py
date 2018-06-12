# coding: utf-8
'''
Miscellaneous utilities.
'''

import sys
import logging

from traceback import format_tb

from .exceptions import Failed

class trying:
	'''
	A context for operations that are prone to failure (i.e. tests and setup 
	operations).
	'''

	def __init__(self, label):
		self.label = label

	def __enter__(self):
		print(self.label)

	def __exit__(self, type, value, traceback):
		if traceback and not isinstance(value, SystemExit):
			print(format_exception(value))
			print('Failed')
			sys.exit(1)
		else:
			print('Done')

	@classmethod
	def fail(cls, message=None):
		'''Fail the attempt.'''
		raise Failed(message)

def create_callback_registrar(loop_arg=False):
	'''
	Create and return a callback registration decorator. Registred callbacks
	are invoked with the `invoke` callable attribute of the decorator.
	'''
	#	Create a list to contain registered callbacks.
	registered = list()

	#	Define the registrar decorator to be returned.
	def registrar(func):
		registered.append(func)
		return func

	#	Define an invocation function and attach it to the registrar.
	if loop_arg:
		def invoker(arg):
			for callback in registered:
				arg = callback(arg)
			return arg
	else:
		def invoker(*args, **kwargs):
			for callback in registered:
				callback(args, kwargs)
		
	registrar.invoke = invoker

	return registrar

def logger(name):
	'''Create and return a logger.'''
	return logging.getLogger(name)

def format_exception(ex):
	'''Format an exception traceback as a string.'''
	#	Create the traceback string.
	traceback = (''.join(format_tb(ex.__traceback__))).strip()
	#	Improve whitepace.
	traceback = traceback.replace('\n    ', '\n\t').replace('\n  ', '\n')

	#	Return fully formatted representation.
	return '%s: %s\n%s'%(ex.__class__.__name__, ex, traceback)

def cached_property(meth):
	'''
	A decorator for properties with a significant execution cost. The return
	value of the initial access is cached and returned to subsequent callers.
	'''
	#	Create the cache.
	cache = []
	
	#	Define the cache-checking retrieval.
	def retrieval(self):
		if not cache:
			cache[0].append(meth(self))
		return cache[0]
	
	#	Return as a property.
	return property(retrieval)
