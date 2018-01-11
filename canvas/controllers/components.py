#	coding utf-8
'''
Components are embedded within controllers
'''

from ..exceptions import UnsupportedMethod
from ..core.assets import render_template

class Component:
	'''
	Embedded within `Controller`s
	'''
	
	def __init__(self, name, controllers):
		'''
		:name The name of the component. Used to identify
		:controllers A list of routes whose controllers should 
			contain this component
		'''
		self.name = name

		#	Normalize routes
		for i, controller in enumerate(controllers):
			if not controller.startswith('/'):
				controllers[i] = f'/{controller}'
		self.controllers = controllers

	def check(self, ctx):
		'''
		Check a request context and raise an exception (generally
		an `HTTPException`) if this component does not want to be placed 
		for that request.

		Raising an exception is used in favor of a boolean return
		because if a POST is addressed to this component, the exception
		lets us formulate a clear response as to why this component
		wouldn't recieve it
		'''
		pass
	
	def handle_get(self, ctx):
		'''
		Handle a get request addressed to this component
		and return some information
		'''
		raise UnsupportedMethod()

	def handle_post(self, ctx):
		'''
		Handle a post request addressed to this component
		and perform some action
		'''
		raise UnsupportedMethod()

class PageComponent(Component):
	'''
	Embedded within `Page`s
	'''

	def __init__(self, name, pages, template=None, dependencies=[], 
			library_dependencies=[], **super_kwargs):
		'''
		:name The name of the component. Used to identify
		:controllers A list of routes whose pages should 
			contain this component
		:template The template (defaults to `name`)
		:dependencies 1st party JavaScript/CSS to be included on
			the page
		:library_dependencies 3rd party JavaScript/CSS to be 
			included on the page
		:super_kwargs Other arguments passed to `super()`
		'''
		super().__init__(name, pages, **super_kwargs)
		self.dependencies = dependencies
		self.library_dependencies = library_dependencies
		self.template = 'components/%s.html'%(name if template is None else template)
	
	def render(self, ctx):
		'''
		Return the rendered template for this component
		'''
		return render_template(self.template, template_params={
			**ctx,
			**{
				'__component__': self
			}
		})
