#	coding utf-8
'''
Jinja template rendering.
'''

import os

from htmlmin import minify as minify_html

from ..plugins import get_path_occurrences
from .jinja_extensions import CanvasJinjaEnvironment

_render_environ = None
@callback.pre_init
def create_environment():
	'''
	Create the global render environment.
	'''
	global _render_environ
	
	#	Get all base template folder paths.
	load_paths = get_path_occurrences(os.path.join('assets', 'templates'), filter=os.path.isdir)
	#	Create.
	_render_environ = CanvasJinjaEnvironment(load_paths)
del create_environment

def render_template(template_path, minify=None, template_params={}, response=False, status=200, headers={}):
	'''
	Render a Jinja2 template.
	
	:template_path The path of the template to render, 
		below `/templates`.
	:minify Whether or not to minify the template as HTML.
		By default will only minify .html files.
	:template_params An optional dictionary of global 
		variables for the render context.
	:response Whether to return a response tuple.
	:status The status code for the response, if `response` 
		is true.
	:headers The header dictionary for the response, 
		if `response` is true.
	'''
	#	Render.
	rendered = _render_environ.get_template(template_path).render(template_params)

	if minify is None:
		#	Check if the template is an HTML file.
		minify = template_path.endswith('.html')

	if minify:
		#	Minify.
		rendered = minify_html(rendered, remove_all_empty_space=True)

	if not response:
		#	Return the rendered template as a string.
		return rendered

	#	Return a response tuple with the rendered
	#	template as the response data.
	return rendered, status, headers, 'text/html'
