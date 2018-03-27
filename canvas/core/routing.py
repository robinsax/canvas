#	coding utf-8
'''
Routing management.
'''

import re

from ..exceptions import NotFound
from ..callbacks import define_callback_type, invoke_callbacks

define_callback_type('router', arguments=[dict])

_route_map = dict()

def create_routing(route_map):
	global _route_map

	invoke_callbacks('router', route_map)

	_route_map = route_map

def resolve_route(real_route):
	controller, real_variables = None, None
	
	real_parts = real_route.split('/')
	for route in _route_map:
		parts = route.split('/')
		if len(real_parts) != len(parts):
			continue

		matches, variables = True, dict()
		for part, real_part in zip(parts, real_parts):
			if part == real_part:
				continue
			
			variable_defn = re.match(r'<(.*?:)?(.*?)>', part)
			if variable_defn:
				typing = variable_defn.group(1)
				if typing:
					try:
						conversion = {
							'int': lambda x: int(x)
						}[typing[:-1]]

						real_part = conversion(real_part)
					except:
						matches = False
						break
				variables[variable_defn.group(2)] = real_part
			else:
				matches = False
				break

		if matches:
			controller = _route_map[route]
			real_variables = variables
			break

	if controller is None:
		raise NotFound(real_route)

	return controller, variables
