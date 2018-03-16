#	coding utf-8
'''
Routing management.
'''

from ..exceptions import NotFound
from ..callbacks import define_callback_type, invoke_callbacks

define_callback_type('router', arguments=[dict])

_route_map = dict()

def create_routing(route_map):
	global _route_map

	invoke_callbacks('router', route_map)

	_route_map = route_map

def controller_at(route):
	if route not in _route_map:
		raise NotFound(route)

	return _route_map[route]
