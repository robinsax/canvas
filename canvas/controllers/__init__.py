#	coding utf-8
'''
TODO
'''

import types

from ..exceptions import (
	UnsupportedMethod, 
	APIRouteDefinitionError,
	NotFound,
	ComponentNotFound
)
from ..utils import WrappedDict, register, get_registered, call_registered
from ..core.thread_context import get_thread_context
from ..core.assets import render_template, markup
from .components import *
from .. import config

__all__ = [
	'Controller',
	'Page',
	'Component',
	'create_everything',
	'get_controller',
	'get_component'
]

GLOBAL_DEPS = config['client_globals']

class Controller:
	'''The base controller object to be extended'''

	def __init__(self, route, grab_components=[], 
			block_components=[]):
		'''
		:route The route for this controller to serve
		:grab_components A list of components to get (that
			aren't themselves targeting this controller)
		:block_components A list of components not to grab,
			even if the are targeting this route
		'''
		if not route.startswith('/'):
			route = f'/{route}'
		self.route = route

		self.grab_components = grab_components
		self.block_components = block_components
		self.components = {}	#	Placeholder
	
	def get_components(self, ctx):
		'''Return all components that wanted to be placed'''
		current = []
		for name in self.components:
			component = self.components[name]
			try:
				component.check(ctx)
				call_registered('callback:pre_component_dispatch', component, ctx)
			except: continue
			current.append(component)
		return current

	def get(self, ctx):
		'''
		Returns some information
		'''
		raise UnsupportedMethod()

	def post(self, ctx):
		'''
		Performs some action and returns the result
		'''
		raise UnsupportedMethod()

class Page(Controller):
	'''The base page object to be extended'''

	def __init__(self, route, name, dependencies=[], library_dependencies=[], 
			template=None, template_params={}, description=config['description'],
			**super_kwargs):
		'''
		:route The route to serve
		:name The displayed name of the page
		:template The template name (default is `route`)
		:dependencies 1st party JavaScript/CSS to be included
		:library_dependencies 3rd party JavaScript/CSS to be included 
		:template_params A dict of additional parameters 
			to pass to this pages' template on render (for 
			example `form_model`). Lambda values will be
			invoked at render time with `vars` as an argument
		:super_kwargs Arguments to pass to the `Controller`
			constructor
		'''
		super().__init__(route, **super_kwargs)
		self.template = 'pages/%s.html'%(template if template is not None else route)
		self.name = name
		self.dependencies = GLOBAL_DEPS['dependencies'][:] + dependencies
		self.library_dependencies = GLOBAL_DEPS['library_dependencies'][:] + library_dependencies
		self.template_params = template_params

	#	TODO: Better
	def collect_dependencies(self, ctx):
		d, ld = (self.dependencies[:], self.library_dependencies[:])
		for component in self.get_components(ctx):
			d += component.dependencies
			ld += component.library_dependencies
		return d, ld

	def render_component(name):
		ctx = get_thread_context()
		for component in self.get_components(ctx):
			if component.name == name:
				return markup(component.render(ctx))
		return None

	def render_components(self):
		ctx = get_thread_context()
		rendered = []
		for component in self.get_components(ctx):
			rendered.append(component.render(ctx))
		return markup(''.join(rendered))

	def get(self, ctx):
		'''
		Return the rendered template for this page
		'''

		#	Call generators in template_params
		resolved_params = {}
		for k, v in self.template_params.items():
			if isinstance(v, types.LambdaType):
				v = v(ctx)
			resolved_params[k] = v

		return render_template(self.template, response=True, template_params={
			**ctx,
			**resolved_params,
			**{
				'render_component': self.render_component,
				'render_components': self.render_components,
				'__page__': self,
				'__ctx__': ctx
			}
		})

class APIEndpoint(Controller):
	'''
	An API endpoint controller. Enforced path prefix of `api/`
	'''

	def __init__(self, route, description='No description available', **super_kwargs):
		'''
		'''
		super().__init__(route, **super_kwargs)
		
		if not self.route.startswith('/api/'):
			raise APIRouteDefinitionError(f'{route} not prefixed with api/')

		self.description = description

@register('template_global')
def get_controller(route_or_controller):
	'''
	Return the controller for the given route or
	the parameter if it's already a controller
	'''
	if isinstance(route_or_controller, Controller):
		return route_or_controller
	if not route_or_controller.startswith('/'):
		route_or_controller = f'/{route_or_controller}'
	return _controllers[route_or_controller]

def get_controllers(filter=lambda: True):
	'''
	Return the list of all controllers
	'''
	return [v for k, v in _controllers.items() if filter(v)]

_controllers = {}
def create_everything():
	global _controllers
	
	#	Create controllers
	classes = get_registered('controller')
	controllers = {}
	for cls in classes:
		inst = cls()
		controllers[inst.route] = inst

	#	Create components
	classes = get_registered('component')
	for cls in classes:
		inst = cls()
		#	Add to controllers
		for route in controllers:
			controller = controllers[route]
			if (not inst.name in controller.block_components) and (
					route in inst.controllers or 
					inst.name in controller.grab_components):
				controller.components[inst.name] = inst

	#	Wrap page component dicts
	for route in controllers:
		controller = controllers[route]
		controller.components = WrappedDict(
				controller.components, ComponentNotFound)
	#	Wrap controller dict
	_controllers = WrappedDict(controllers, NotFound)

