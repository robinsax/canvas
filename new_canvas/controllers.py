#	coding utf-8
'''
Controller registration and management.
'''

from .namespace import export

_definitions = []

class _ControllerDefinition:

	def __init__(self, cls, routes, variant):
		self.cls = cls
		self.routes, self.variant = routes, variant

@export
def controller(*routes, _typ='basic'):
	def controller_wrap(cls):
		definition = _ControllerDefinition(cls, routes, _typ)
		_definitions.append(definition)
		
		return cls
	return controller_wrap

@export
def endpoint(routes):
	return controller(*routes, _typ='endpoint')

@export
def page(routes):
	return controller(*routes, _type='routes')

def create_controllers(route_map):
	for definition in _definitions:
		instance = definition.cls()

		supported_verbs = []
		for verb in ['get', 'post', 'put', 'patch', 'delete', 'options']:
			if hasattr(instance, 'do_{}'.format(verb)):
				supported_verbs.append(verb)
		instance.__verbs__ = supported_verbs

		for route in definition.routes:
			route_map[route] = instance

		#	TODO: Not using variant.
	
	return route_map
