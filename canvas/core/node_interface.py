#	coding utf-8
'''
Node interface.
'''

import os
import execjs

from ..exceptions import AssetError
from ..namespace import export
from .. import __home__
from .asset_directives import apply_directives

_node_interface = None

def create_node_interface():
	global _node_interface
	partner_path = os.path.join(__home__, 'canvas', 'core', 'node_interface.js')
	with open(partner_path) as partner_file:
		partner_source = partner_file.read()
	
	_node_interface = execjs.compile(partner_source)

@export
def transpile_jsx(source):
	if not isinstance(source, str):
		source = source.decode()
	
	source = apply_directives(source)
	
	try:
		source = _node_interface.call('transpile', source)
	except BaseException as ex:
		raise AssetError(str(ex)) from None
	
	return source
