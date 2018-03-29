#	coding utf-8
'''
Misc. utilities.
'''

import logging

from traceback import format_tb

from .namespace import export

@export
def logger(name):
	return logging.getLogger(name)

@export
def format_exception(ex):
	traceback = (''.join(format_tb(ex.__traceback__))).strip().replace('\n    ', '\n\t').replace('\n  ', '\n')
	return '{}: {}\n{}'.format(ex.__class__.__name__, ex, traceback)

@export
def kw_init(*attrs):
	def create_kw_init(cls):
		inner_init = cls.__init__
		def new_init(self, *args, **kwargs):
			for arg, attr in zip(args, attrs):
				setattr(self, attr, arg)

			for name, value in list(kwargs.items()):
				if name not in attrs:
					raise TypeError('Invalid keyword argument %s'%name)
				
				setattr(self, name, value)
				del kwargs[name]

			for name in attrs:
				if getattr(self, name, None) is None:
					setattr(self, name, None)

			inner_init(*args, **kwargs)
		cls.__init__ = new_init
	return create_kw_init
	

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
