#	coding utf-8
'''
Controller base class definition and namespace
generation.
'''

import types

from ..exceptions import (
	UnsupportedMethod, 
	APIRouteDefinitionError,
	NotFound,
	ComponentNotFound
)
from ..utils import (
	WrappedDict, 
	register, 
	get_registered, 
	call_registered
)
from ..core.thread_context import get_thread_context
from ..core.assets import render_template, markup
from .components import *
from .. import config

#	Declare exports.
__all__ = [
	'Controller',
	'Page',
	'APIEndpoint',
	#	Submodule classes.
	'Component',
	'PageComponent',
	#	Functions.
	'create_everything',
	'get_controller'
]

#	TODO: Route mapping.

#	Create an alias to the list of global client 
#	dependencies (to be included with every page).
GLOBAL_DEPS = config['client_dependencies']

class Controller:
	'''
	The base controller class enforces route presence
	and component management.
	'''

	def __init__(self, route, grab_components=[], 
			block_components=[]):
		'''
		Configure the overriding controller class.

		:route The route for this controller, relative 
			to domain root.
		:grab_components The list of components to add to 
			this controller. Components that are targeting
			this controller do not need to be specified.
		:block_components The list of components that are
			targeting this controller but should not be
			added to it.
		'''
		#	Ensure route is prefixed.
		if not route.startswith('/'):
			route = f'/{route}'
		self.route = route

		self.grab_components = grab_components
		self.block_components = block_components

		#	Each controllers components are populated 
		#	by the controller initialization logic.
		self.components = {}
	
	def get_components(self, ctx):
		'''
		Return all components that that didnt raise an 
		exception when their `check()` method was called 
		with the current request context.
		'''
		current = []

		for name, component in self.components.items():
			try:
				#	Allow the component and callbacks to raise 
				#	an exception if they should not be accessible 
				#	during the handling of the current request.
				component.check(ctx)
				call_registered('pre_component_dispatch', component, ctx)
			except: continue
			#	Nothing raised an exception, this component should
			#	be available during the handling of this request.
			current.append(component)

		return current

	def get(self, ctx):
		'''
		The GET request method handler.

		By default raises an exception that causes
		a 405 response code to be returned to the 
		client.
		'''
		raise UnsupportedMethod()

	def post(self, ctx):
		'''
		The POST request method handler.

		By default raises an exception that causes
		a 405 response code to be returned to the 
		client.
		'''
		raise UnsupportedMethod()

class Page(Controller):
	'''
	The base page class implements template rendering
	for GET requests, dependency management, and supporting
	features.
	'''

	def __init__(self, route, title, dependencies=[], library_dependencies=[], 
			template=None, template_params={}, description=config['description'],
			**super_kwargs):
		'''
		Configure the overriding controller class.

		:route The route for this controller, relative to 
			domain root.
		:title The title of the page with which to populate
			the title tag.
		:template The title of this pages template file, without
			the `pages/` prefix and `html` file extension.
		:dependencies A list of non-library client dependencies.
		:library_dependencies A list of library client dependencies.
		:template_params A dictionary of additional parameters 
			for this pages template render context. Lambda values 
			will be invoked at render time with a single parameter; 
			the request context.
		:super_kwargs The `Controller` class constructors 
			keyword arguments.
		'''
		super().__init__(route, **super_kwargs)
		self.title, self.template_params = title, template_params

		#	Collect the dependency lists.
		self.dependencies = GLOBAL_DEPS['dependencies'][:] + dependencies
		self.library_dependencies = GLOBAL_DEPS['library_dependencies'][:] + library_dependencies

		#	Format the template file path and get the default
		#	name (the route) if it wasn't specified.
		self.template = f'pages/{template if template is not None else route}.html'

	def collect_dependencies(self):
		'''
		Return a tuple containing respectively the non-library
		and library client dependencies of this page, given the 
		current request context.
		'''
		#	Retrieve the request context.
		ctx = get_thread_context()

		#	Copy the dependencies lists.
		deps, lib_deps = (self.dependencies[:], self.library_dependencies[:])

		#	Iterate all components and append their dependencies.
		for component in self.get_components(ctx):
			deps += component.dependencies
			lib_deps += component.library_dependencies
		
		return deps, lib_deps

	def render_component(self, name):
		'''
		Render the component with name `name` and return its 
		rendered template as markup, or return `None` if the
		there is no component called `name` available to the
		current request context.
		'''
		#	Retrieve the request context.
		ctx = get_thread_context()

		#	Iterate available components, rendering and
		#	returning if found.
		for component in self.get_components(ctx):
			if component.name == name:
				return markup(component.render(ctx))

		#	No such component; return `None`.
		return None

	def render_components(self):
		'''
		Render each component available given the current 
		request context and return the sum of their rendered 
		templates as markup.
		'''
		#	Retrieve the request context.
		ctx = get_thread_context()

		#	Render all components.
		rendered = []
		for component in self.get_components(ctx):
			rendered.append(component.render(ctx))

		#	List joins are the most efficient string
		#	concatination method in Python.
		return markup(''.join(rendered))
	
	def get(self, ctx):
		'''
		Return a response tuple containing the rendered 
		template for this page.
		'''
		#	Resolve the `template_params` parameters.
		resolved_params = {}
		for k, v in self.template_params.items():
			if isinstance(v, types.LambdaType):
				#	Call to generate a value.
				v = v(ctx)
			resolved_params[k] = v

		#	Invoke rendering with a tuple return value.
		return render_template(self.template, response=True, template_params={
			#	The request context.
			**ctx,
			#	The resolved constructor paramets.
			**resolved_params,
			**{
				#	Canonical component rendering accessors.
				'render_component': self.render_component,
				'render_components': self.render_components,
				#	This page.
				'__page__': self
			}
		})

class APIEndpoint(Controller):
	'''
	The canonical API endpoint controller base class enforces
	a `api/` route prefix and the presence of a description
	to allow intuative endpoint presentation.
	'''

	def __init__(self, route, description='No description available', **super_kwargs):
		'''
		Configure the overriding controller class.

		:route The route for this controller, relative to 
			domain root. Must begin with `'/api/'`.
		:description A human readable description of the endpoint
			in markdown.
		:super_kwargs The `Controller` class constructors 
			keyword arguments.
		'''
		super().__init__(route, **super_kwargs)
		self.description = description
		
		#	Assert route prefix.
		if not self.route.startswith('/api/'):
			raise APIRouteDefinitionError(f'{route} not prefixed with api/')

@register.template_helper
def get_controller(route_or_controller):
	'''
	Return the controller for the given route or
	the parameter if it's already a controller.

	:route_or_controller A controller instance or
		existing route.
	'''
	#	Perform an identify on controllers.
	if isinstance(route_or_controller, Controller):
		return route_or_controller

	#	Ensure the route is properly formatted.
	if not route_or_controller.startswith('/'):
		route_or_controller = f'/{route_or_controller}'
	
	#	Return the controller instance for this route,
	#	or raise an exception if it isn't present.
	return _controllers[route_or_controller]

def get_controllers(filter=lambda: True):
	'''
	Return the list of all controller instances.

	:filter A filter function on controller inclusion.
	'''
	return [v for k, v in _controllers.items() if filter(v)]

#	The global route to controller instance mapping.
_controllers = {}
def create_everything():
	'''
	Create the singleton instance of all controllers and 
	components, then add components to controllers.
	'''
	global _controllers
	
	#	Instantiate a route, controller class instance
	#	mapping.
	controllers = {}
	for cls in get_registered('controller'):
		inst = cls()
		controllers[inst.route] = inst

	#	Create each component, adding the instance to
	#	all valid controllers.
	for cls in get_registered('component'):
		#	Create the instance.
		inst = cls()

		for route, controller in controllers.items():
			#	Check if the controller blocked the component.
			blocked = inst.name in controller.block_components
			#	Check if either the component or controller requested
			#	the component be added.
			add = route in inst.controllers or inst.name in controller.grab_components

			if (not blocked and add):
				#	Add the component to the controller.
				controller.components[inst.name] = inst

	#	Wrap the component dictionary for each controller
	#	to allow a 454 (canvas defined; Component Not Found)
	#	to be returned to the client when a nonexistant controller
	#	is addressed in a request.
	for route, controller in controllers.items():
		controller.components = WrappedDict(controller.components, 
				ComponentNotFound)

	#	Create the global route to controller instance mapping,
	#	replacing `KeyError` with a HTTP-coded exception that
	#	causes a 404 status code to be returned to the client.
	_controllers = WrappedDict(controllers, NotFound)
