#	coding utf-8
'''
Root namespace management.
'''

import sys

__all__ = []
_namespace = sys.modules['canvas']
_namespace.__all__ = __all__

def export(name_or_item):
	def do_export(item, name):
		if name is None:
			name = item.__name__
		
		setattr(_namespace, name, item)
		__all__.append(name)
		return item
	
	if isinstance(name_or_item, str):
		def export_wrap(item):
			return do_export(item, name_or_item)
		return export_wrap
	else:
		return do_export(name_or_item, name_or_item.__name__)
