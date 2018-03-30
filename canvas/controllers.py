#	coding utf-8
'''
Controller registration and management.
'''

from .exceptions import IllegalEndpointRoute
from .namespace import export
from .configuration import config
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

		params.update({
			'__route__': context.url.route
		})
		return create_webpage(self.__template__, params, code=code, 
				headers=headers)

class _ControllerDefinition:

	def __init__(self, cls, routes, attrs):
		self.cls = cls
		self.routes, self.attrs = routes, attrs

@export
def controller(*routes, _destiny=Controller, **attrs):
	def controller_wrap(cls):
		patched = patch_type(cls, _destiny)
		definition = _ControllerDefinition(patched, routes, **attrs)
		_definitions.append(definition)
		
		return patched
	return controller_wrap

@export
def endpoint(*routes, **attrs):
	route_prefix = '/%s'%config.customization.api_route_prefix
	for route in routes:
		if not route.startswith(route_prefix):
			raise IllegalEndpointRoute(route)

	return controller(*routes, _destiny=Endpoint, **attrs)

@export
def page(*routes, template=None, **attrs):
	if template is None:
		template = '%s.html'%routes[0][1:]
	
	attrs['template'] = template

	return controller(*routes, _destiny=Page, **attrs=attrs)

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
