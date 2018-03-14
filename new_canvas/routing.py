#	coding utf-8
'''
Routing management.
'''

from .callbacks import define_callback_type, invoke_callbacks

define_callback_type('router', arguments=[dict])

def update_routing(route_map):
	invoke_callbacks('router', route_map)
