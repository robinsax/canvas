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

def patch_type(cls, destiny):
	if issubclass(cls, destiny):
		return cls

	class Patched(cls, destiny): pass
	Patched.__name__ = cls.__name__

	return Patched
