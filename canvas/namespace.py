#	coding utf-8
'''
Root namespace management.
'''

import sys

_root_namespace = sys.modules['canvas']
_root_namespace.__all__ = []

_ext_namespace = sys.modules['ext']
_ext_namespace.__all__ = []

def _provide_export(name_or_item, namespace):
	def do_export(item, name):
		if name is None:
			name = item.__name__
		
		setattr(namespace, name, item)
		namespace.__all__.append(name)
		return item
	
	if isinstance(name_or_item, str):
		def export_wrap(item):
			return do_export(item, name_or_item)
		return export_wrap
	else:
		return do_export(name_or_item, name_or_item.__name__)

def export(name_or_item):
	return _provide_export(name_or_item, _root_namespace)

def export_ext(name_or_item)
	return _provide_export(name_or_item, _ext_namespace)
