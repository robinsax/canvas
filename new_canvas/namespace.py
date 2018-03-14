#	coding utf-8
'''
Namespace management.

The namespace created here becomes the root canvas namespace before init-time.
'''

import sys

#	The namespace staging list.
__all__ = []
_namespace = sys.modules['new_canvas']
_namespace.__all__ = __all__

def export(name_or_item):
	def do_export(item, name):
		if name is None:
			name = item.__name__
		
		print('Exporting ' + name)
		setattr(_namespace, name, item)
		__all__.append(name)
		return item
	
	if isinstance(name_or_item, str):
		def export_wrap(item):
			return do_export(item, name_or_item)
		return export_wrap
	else:
		return do_export(name_or_item, name_or_item.__name__)
