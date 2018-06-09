#	coding utf-8
'''
Miscellaneous utilities.
'''

import logging

from traceback import format_tb

def create_callback_registrar():
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
	def invoker(*args, **kwargs):
		for callback in registered:
			callback(args, kwargs)
	registerar.invoke = invoker

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
			return getattr(self, cache[0])
		else:
			return cache[0] = meth(self)
	
	#	Return as a property.
	return property(retrieval)
