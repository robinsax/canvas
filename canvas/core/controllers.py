# coding: utf-8
'''
Controller base type definitions and registrars. Since registrars implicitly
cause inheritance of their associated controller type, parent classes need
not be specified when defining controller classes.
'''

from ..exceptions import IllegalEndpointRoute
from ..configuration import config
from ..utils import logger
from .. import __verbs__
from .views import PageView
from .request_context import RequestContext
from .responses import create_page

#	Create a log.
log = logger(__name__)

class _ControllerRegistration:
	'''A class used internaly for controller registratiom management.'''
	instances = list()

	def __init__(self, cls, routes, attrs):
		self.cls, self.routes, self.attrs = cls, routes, attrs

	@classmethod
	def create(cls, *args):
		'''Create and store a new controller registration.'''
		instance = _ControllerRegistration(*args)
		cls.instances.append(instance)
		return instance

class Controller:
	'''The base controller class.'''
	pass

class Endpoint(Controller):
	'''
	The base API endpoint class, whose routes must be rooted in the configured
	API region.
	'''
	pass

class Page(Controller):
	'''
	The base webpage controller class. Generates an associated view which is
	rendered to obtain a response.
	'''
	
	def on_get(self, context):
		return self.render()

	def get_view(self, title=None, description=None, page_data=dict()):
		'''Return the root view to be rendered.'''
		if not title:
			title = self.__title__
		if not description:
			description = self.__description__

		#	TODO: Lazy hack.
		context = RequestContext.get()
		return PageView.resolved(title, description, self.get_assets(context), page_data)

	def get_assets(self, context):
		return self.__assets__

	def render(self, title=None, description=None, page_data=dict(), code=200, headers=dict()):
		'''Return the rendered view for this page as a response tuple.'''
		view = self.get_view(title, description, page_data)
		return create_page(view, code, headers)

def controller(*routes, _destiny=Controller, **attrs):
	'''
	The trivial controller registration decorator. Under most circumstances, 
	this should not be used directly.
	::routes A list for routes for this controller to service.
	::_destiny The class that the decorated controller is destined to inherit
		from.
	::attrs Additional attributes, to be attached to the singleton instance
		protected with double underscores.
	'''
	
	def controller_inner(cls):
		#	Create a patched type of the controller and its destiny.
		patched = type(cls.__name__, (cls, _destiny), dict())
		if 'expects' not in attrs:
			attrs['expects'] = '*'
		#	Create this registration.
		_ControllerRegistration.create(patched, routes, attrs)

		return patched
	return controller_inner

def endpoint(*routes, expects='json', **attrs):
	'''
	The API endpoint controller registration decorator.
	::routes A list for routes for this controller to service.
	::expects The secondary type of the expected mimetype.
	'''
	#	Assert all routes are valid.
	route_prefix = '/%s'%config.route_prefixes.api
	for route in routes:
		if not route.startswith(route_prefix):
			raise IllegalEndpointRoute(route)

	#	Add the content type expectation to attrs for attachment.
	attrs['expects'] = expects
	return controller(*routes, _destiny=Endpoint, **attrs)

def page(*routes, title=str(), description=str(), assets=tuple(), **attrs):
	'''
	The page controller registration decorator.
	::routes A list for routes for this controller to service.
	::title The title of the page.
	::description An optional description of the page.
	::assets An iterable of JavaScript and CSS asset paths to be included on 
		the page.
	'''
	#	Add known parameters to attrs for attachment.
	attrs.update({
		'title': title,
		'description': description,
		'assets': assets
	})
	return controller(*routes, _destiny=Page, **attrs)

def create_controllers():
	'''Return a list containing an instance of each registered controller.'''
	created = list()
	for registration in _ControllerRegistration.instances:
		#	Create the instance.
		controller = registration.cls()
		controller.__routes__ = registration.routes
		#	Assign all attributes.
		for key, value in registration.attrs.items():
			setattr(controller, '__%s__'%key, value)

		#	Check and store supported verbs.
		supported_verbs = list()
		for verb in __verbs__:
			if hasattr(controller, 'on_%s'%verb):
				supported_verbs.append(verb)
		controller.__verbs__ = supported_verbs

		log.debug('Created controller %s (Verbs: %s, Routes: %s)'%(
			controller.__class__.__name__, supported_verbs, registration.routes
		))
		created.append(controller)
	return created
