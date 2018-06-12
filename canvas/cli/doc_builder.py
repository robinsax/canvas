# coding: utf-8
'''
Documentation generation.
'''

import inspect

from . import launcher

@launcher('doc',
	argspec='<?plugin>',
	description='Build documentation for canvas, or a plugin if one is specified'
)
def build_docs():
	return True
