#	coding utf-8
'''
Jinja template actualization
'''

import os
import jinja2

from urllib import parse

from htmlmin import minify as minify_html

from jinja2 import Markup
from jinja2.exceptions import TemplateNotFound

from ...exceptions import MacroParameterError, UnsupportedEnformentMethod
from ...utils import register
from ...model import get_constraint
from ..plugins import get_path_occurrences
from .jinja_extensions import CanvasJinjaEnvironment
from ... import config

_render_environ = None
@register('callback:pre_init')
def create_environment():
	global _render_environ
	
	#	Get all template folder paths
	load_paths = get_path_occurrences(os.path.join('assets', 'templates'), filter=os.path.isdir)
	_render_environ = CanvasJinjaEnvironment(load_paths)
del create_environment

def render_template(template_path, response=False, minify=None, status=200, headers={}, template_globals={}):
	'''
	Renders a Jinja2 template.
	:template_path The path of the template to render, below `/templates`
	:minify Whether or not to minify the template as HTML
	:template_globals An optional dictionary of variables for the render context
	'''
	#	Render
	rendered = _render_environ.get_template(template_path).render(template_globals)
	if minify is None:
		#	Guess
		minify = template_path.endswith('.html')
	if minify:
		#	Minify
		rendered = minify_html(rendered, remove_all_empty_space=True)
	if not response:
		return rendered
	return rendered, status, headers, 'text/html'

@register('template_filter')
def markup(text):
	'''
	Transform the string `text` into markup 
	that is not escaped when rendered in a 
	template.

	Available as a template filter.
	
	__Note__: Beware of XSS vulerabilities here.
	'''
	return Markup(text)

@register('template_filter')
def markdown(markdown, return_markup=True):
	'''
	Render a string as markdown.

	Available as a template filter.

	:markdown The string to render as markdown
	:return_markup Whether or not to return a markup object
		that will not be escaped when rendered
	'''
	rendered = markdown(markdown)
	if return_markup:
		return markup(rendered)
	return rendered

@register('template_filter')
def uri_encode(s):
	return parse.quote(s)

@register('template_global')
def parameter_error(msg):
	'''
	Raise a `MacroParameterError` from within
	a template macro call
	'''
	raise MacroParameterError(msg)
del parameter_error

#	TODO: Fix both below

@register('template_global')
def get_client_validator(name):
	origin = get_constraint(name)
	if origin is not None:
		try:
			return {
				'repr': origin.as_client_parsable(),
				'error': origin.error_message
			}
		except UnsupportedEnformentMethod: pass
	
	return {
		'repr': 'none:',
		'error': ''
	}
del get_client_validator

@register('template_global')
def describe_model_attr(model, attr):
	col = model.__schema__[attr]
	return {
		'type': col.type.input_type,
		'name': attr,
		'label': ' '.join(attr.split('_')).title(),
		'validator': None if len(col.constraints) == 0 else col.constraints[0].name
	}
del describe_model_attr