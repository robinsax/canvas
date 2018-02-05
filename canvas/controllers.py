#	coding utf-8
'''
`Controller` base class definitions and namespace generation.
'''

import types

from .exceptions import (
	UnsupportedMethod, 
	APIRouteDefinitionError,
	NotFound
)
from .utils import (
	WrappedDict, 
	register, 
	get_registered, 
	call_registered,
	markup
)
from .core.thread_context import get_thread_context
from .core.assets import render_template
from . import config

#	Declare exports.
__all__ = [
	'Controller',
	'Page',
	'APIEndpoint',
	'Redirector',
	#	Submodule classes.
	'Component',
	'PageComponent',
	#	Functions.
	'create_everything',
	'get_controller'
]

#	Create an alias to the list of global client dependencies (to be included 
#	with every page).
CLIENT_DEPENDENCIES = config['client_dependencies']

class Controller:
	'''
	`Controller`s are singleton request handlers attached to a specific route.
	They have instance methods for each of the (supported) request methods, 
	which are passed a sole parameter; the request context.

	The request context is a dictionary containing the request parameters 
	and headers (`request`, `headers`), a database session (`session`), and the
	cookie session (`cookie`) as a dictionary.

	Plugins can extend the request context with the `context_created` callback.
	'''

	def __init__(self, route):
		'''
		Configure the overriding controller class.
		
		:route The route for this controller, relative to domain root.
		'''
		#	Ensure route is prefixed.
		if not route.startswith('/'):
			route = f'/{route}'
		self.route = route
	
	def get(self, ctx):
		'''
		The GET request method handler.

		By default raises an exception that causes a `405` response to be 
		returned to the client.
		'''
		raise UnsupportedMethod()

	def post(self, ctx):
		'''
		The POST request method handler.

		By default raises an exception that causes a `405` response to be 
		returned to the client.
		'''
		raise UnsupportedMethod()

class Page(Controller):
	'''
	`Page`s are web page `Controller`s, which serve HTML pages when sent a GET
	request.

	The `Page` class implements Jinja template ownership rendering as well as 
	metadata and dependency management.

	*Note*: All `Page` templates should be rendered while by calling 
	`super().get()`, as it provides parameters required by the base template.
	'''

	def __init__(self, route, title, dependencies=[], library_dependencies=[], 
			template=None, template_params={}, description=config['description']):
		'''
		Configure the overriding controller class.

		:route The route for this controller, relative to domain root.
		:title The title with which to populate the title tag.
		:template The title of this `Page`s' template file, without the `pages/` 
			prefix.
		:dependencies A list of non-library client dependencies.
		:library_dependencies A list of library client dependencies.
		:template_params A dictionary of additional parameters for this `Page`s 
			template rendering context. Lambda values will be invoked at render 
			time with a single parameter; the request context.
		:description The content of the `description` field for this `Page`.
		'''
		super().__init__(route)
		self.title, self.template_params = title, template_params

		#	Collect the dependency lists.
		self.dependencies = CLIENT_DEPENDENCIES['dependencies'][:] + dependencies
		self.library_dependencies = CLIENT_DEPENDENCIES['library_dependencies'][:] + library_dependencies

		#	Format the template file path. Use the route as the template name 
		#	if it wasn't otherwise specified.
		if template is None:
			template = f'{route}.html'
		self.template = f'pages/{template}'

	def get(self, ctx):
		'''
		Return a response tuple containing this `Page`s rendered template.
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
			#	The resolved constructor parameters.
			**resolved_params,
			**{
				#	This page.
				'__page__': self
			}
		})

class APIEndpoint(Controller):
	'''
	`APIEndpoint`s are canonical endpoint `Controller`s that enforce an `api/` 
	route prefix.
	'''

	def __init__(self, route, description=''):
		'''
		Configure the overriding controller class.

		:route The route for this controller, relative to domain root. Must 
			begin with `'/api/'`.
		:description A human readable description of the endpoint (in Markdown).
		'''
		super().__init__(route)
		self.description = description
		
		#	Assert route is prefixed as it is used by the request handler to
		#	determine error response format.
		if not self.route.startswith('/api/'):
			raise APIRouteDefinitionError(f'{route} not prefixed with api/')

class Redirector(Controller):
	'''
	A controller that redirects all requests to another URL.
	'''

	def __init__(self, route, target_route, code=302):
		super().__init__(route)
		self.target_route = target_route
		self.code = 302

	def get(self, ctx):
		from .core import redirect_to
		redirect_to(self.target_route, self.code)
	
	def post(self, ctx):
		from .core import redirect_to
		redirect_to(self.target_route, self.code)

@register.template_helper
def get_controller(route):
	'''
	Return the controller for the given route.
	'''
	#	Ensure the route is properly formatted.
	if not route.startswith('/'):
		route = f'/{route}'
	
	#	Return the controller instance for this route, or raise an exception 
	#	if it isn't present.
	return _controllers[route]

def get_controllers(filter=lambda v: True):
	'''
	Return the list of all controller instances.

	:filter A filter function on controller inclusion.
	'''
	return [v for k, v in _controllers.items() if filter(v)]

#	The global route to controller instance mapping.
_controllers = None
def create_everything():
	'''
	Create the singleton instance of all controllers.
	'''
	global _controllers
	
	#	Instantiate a route, controller class instance mapping.
	controllers = {}
	for cls in get_registered('controller'):
		inst = cls()
		controllers[inst.route] = inst
	
	#	Wrap and assign the global controller mapping.
	_controllers = WrappedDict(controllers, NotFound)
