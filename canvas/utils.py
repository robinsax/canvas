#	coding utf-8
'''
Misc. utilities.
'''

import logging

from traceback import format_tb

from .namespace import export

@export
def logger(name):
	log = logging.getLogger(name)
	return log

@export
def format_exception(ex):
	traceback = (''.join(format_tb(ex.__traceback__))).strip().replace('\n    ', '\n\t').replace('\n  ', '\n')
	return '{}: {}\n{}'.format(ex.__class__.__name__, ex, traceback)

def patch_type(cls, destiny):
	if issubclass(cls, destiny):
		return cls

	class Patched(cls, destiny):
		def __repr__(self):
			return '<%s(%s) at 0x%s>'%(
				cls.__name__, 
				destiny.__name__, 
				hex(id(self))
			)
	Patched.__name__ = cls.__name__

	return Patched

@export
def cached_property(meth):
	protected = '_%s'%meth.__name__
	def retrieval(self):
		if hasattr(self, protected):
			return getattr(self, protected)
		else:
			value = meth(self)
			setattr(self, protected, value)
			return value
	
	return property(retrieval)
