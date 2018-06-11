# coding: utf-8
'''
Controller base type definitions and registrars. Since registrars implicitly
cause inheritance of their associated controller type, parent classes need
not be specified when defining controller classes.
'''

from ..exceptions import IllegalEndpointRoute
from ..configuration import config
from ..utils import logger
from .request_context import RequestContext
from .responses import create_page
from .forms import serialize_form_models
from . import __verbs__

_definitions = list()

log = logger(__name__)

class Controller: pass

class Endpoint(Controller): pass

class Page(Controller):
	
	def on_get(self, context):
		return self.render(context)

	def render(self, code=200, headers=dict()):
		return create_page(self.__view__, code, headers)

class _ControllerDefinition:

	def __init__(self, cls, routes, attrs):
		self.cls = cls
		self.routes, self.attrs = routes, attrs

@export
def controller(*routes, _destiny=Controller, **attrs):
	def controller_wrap(cls):
		patched = type(cls.__name__, (cls, _destiny), dict())
		definition = _ControllerDefinition(patched, routes, attrs)
		_definitions.append(definition)
		
		return patched
	return controller_wrap

@export
def endpoint(*routes, expects='json', **attrs):
	route_prefix = '/%s'%config.customization.api_route_prefix
	for route in routes:
		if not route.startswith(route_prefix):
			raise IllegalEndpointRoute(route)

	attrs['expects'] = expects
	return controller(*routes, _destiny=Endpoint, **attrs)

@export
def page(*routes, template=None, models=tuple(), **attrs):
	if template is None:
		template = '%s.html'%routes[0][1:]
	
	attrs.update({
		'template': template,
		'models': models
	})
	return controller(*routes, _destiny=Page, **attrs)

@page('/', template='welcome.html')
class DefaultWelcomePage: pass

def create_controllers():
	route_map = dict()
	for definition in _definitions:
		instance = definition.cls()
		for key, value in definition.attrs.items():
			setattr(instance, '__%s__'%key, value)

		supported_verbs = []
		for verb in __verbs__:
			if hasattr(instance, 'on_%s'%verb):
				supported_verbs.append(verb)
		instance.__verbs__ = supported_verbs

		for route in definition.routes:
			route_map[route] = instance
		
		log.debug('Created controller %s (Verbs: %s, Routes: %s)', instance.__class__.__name__, supported_verbs, definition.routes)
	
	return route_map
