#	coding utf-8
'''
Components can be added to controllers to allow
request-handling functionality to be easily 
duplicated between routes.
'''

from ..exceptions import UnsupportedMethod
from ..core.assets import render_template

__all__ = [
	'Component',
	'PageComponent'
]

class Component:
	'''
	The base component class enforces name and targeted 
	controller list presence.
	'''
	
	def __init__(self, name, controllers):
		'''
		Configure the overriding component.

		:name A unique name for the component used for its
			identification.
		:controllers A list of controller routes to which
			this component should be added.
		'''
		self.name = name

		#	Ensure correct route format.
		for i, controller in enumerate(controllers):
			if not controller.startswith('/'):
				controllers[i] = f'/{controller}'
		self.controllers = controllers

	def check(self, ctx):
		'''
		Check a request context and raise a subclass of `Unavailable` 
		if this component does not want to be available for the 
		handling of that request.

		Relying on an exception raise allows an informative error 
		to be supplied to the client for requests where this component is 
		addressed.

		By default will never raise an exception.
		'''
		pass
	
	def handle_get(self, ctx):
		'''
		Handle a GET request addressed to this component.
		'''
		raise UnsupportedMethod()

	def handle_post(self, ctx):
		'''
		Handle a POST request addressed to this component.
		'''
		raise UnsupportedMethod()

class PageComponent(Component):
	'''
	The base page component class implements template 
	rendering and dependency management.
	'''

	def __init__(self, name, pages, template=None, dependencies=[], 
			library_dependencies=[], **super_kwargs):
		'''
		Configure the overriding component.

		:name A unique name for the component used for its
			identification.
		:controllers A list of controller routes to which
			this component should be added.
		:template The name of this component's template file, without
			the `components/` prefix and `html` file extension.
		:dependencies A list of non-library client dependencies.
		:library_dependencies A list of library client dependencies.
		:super_kwargs The `Component` class constructors 
			keyword arguments.
		'''
		super().__init__(name, pages, **super_kwargs)
		self.dependencies = dependencies
		self.library_dependencies = library_dependencies

		#	Format the template file path and get the default
		#	name (the component name) if it wasn't specified.
		self.template = 'components/%s.html'%(name if template is None else template)
	
	def render(self, ctx):
		'''
		Return the rendered template for this component.
		'''
		return render_template(self.template, template_params={
			**ctx,
			**{
				'__component__': self
			}
		})
