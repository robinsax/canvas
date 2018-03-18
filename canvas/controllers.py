#	coding utf-8
'''
Controller registration and management.
'''

from .exceptions import IllegalEndpointRoute
from .namespace import export
from .utils import logger, patch_type
from .core.request_context import RequestContext
from .core.responses import create_webpage

_definitions = []

log = logger(__name__)

class Controller: pass

class Endpoint(Controller): pass

class Page(Controller):

	def on_get(self, context):
		return self.render()

	def render(self, params=dict(), code=200, headers=dict()):
		context = RequestContext.get()

		return create_webpage(self.__template__, {
			**params,
			**{
				'__route__': context.url.route
			}
		}, code=code, headers=headers)

class _ControllerDefinition:

	def __init__(self, cls, routes, attrs):
		self.cls = cls
		self.routes, self.attrs = routes, attrs

@export
def controller(*routes, _destiny=Controller, _attrs=dict()):
	def controller_wrap(cls):
		patched = patch_type(cls, _destiny)
		definition = _ControllerDefinition(patched, routes, _attrs)
		_definitions.append(definition)
		
		return patched
	return controller_wrap

@export
def endpoint(*routes):
	route_prefix = '/%s'%config.customization.api_route_prefix
	for route in routes:
		if not route.startswith(route_prefix):
			raise IllegalEndpointRoute(route)
	return controller(*routes, _destiny=Endpoint)

@export
def page(*routes, template=None):
	return controller(*routes, _destiny=Page, _attrs={
		'template': template
	})

@page('/', template='welcome.html')
class DefaultWelcomePage: pass

def create_controllers():
	route_map = dict()
	for definition in _definitions:
		instance = definition.cls()
		for key, value in definition.attrs.items():
			setattr(instance, '__%s__'%key, value)

		supported_verbs = []
		for verb in ['get', 'post', 'put', 'patch', 'delete', 'options']:
			if hasattr(instance, 'on_%s'%verb):
				supported_verbs.append(verb)
		instance.__verbs__ = supported_verbs

		for route in definition.routes:
			route_map[route] = instance

		log.debug('Created controller %s (Verbs: %s, Routes: %s)', instance.__class__.__name__, supported_verbs, definition.routes)
	
	return route_map
