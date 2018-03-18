#	coding utf-8
'''
Node interface.
'''

import os
import re
import execjs

from ..exceptions import AssetError
from ..namespace import export
from .plugins import get_path_occurrences
from .. import HOME

_node_interface = None

def create_node_interface():
	global _node_interface
	partner_path = os.path.join(HOME, 'canvas', 'core', 'node_interface.js')
	with open(partner_path) as partner_file:
		partner_source = partner_file.read()
	
	_node_interface = execjs.compile(partner_source)

@export
def transpile_jsx(source):
	if not isinstance(source, str):
		source = source.decode()
	
	for include_directive in re.finditer(r'//\s+cv::include\s+(.+)\s*?\n', source):
		include = '%s.jsx'%include_directive.group(1).strip()

		occurrences = get_path_occurrences('assets', 'client', include)
		if len(occurrences) == 0:
			raise AssetError('Illegal include: %s'%include)
		
		with open(occurrences[0], 'r') as include_file:
			include_source = include_file.read()

		source = source.replace(include_directive.group(0), include_source + '\n')
	
	try:
		source = _node_interface.call('transpile', source)
	except BaseException as ex:
		raise AssetError(str(ex)) from None
	
	return source
