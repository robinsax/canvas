#	coding utf-8
'''
Jinja extentions and template actualization.
'''

from htmlmin import minify as minify_html

from ...namespace import export
from ...configuration import config
from ..plugins import get_path_occurrences

_extensions = []
_helpers = dict()
_filters = dict()
_render_environment = None

@export
def jinja_extension(extension):
	_extensions.append(extension)
	return extension

@export
def template_helper(func):
	_helpers[func.__name__] = func
	return func

@export
def template_filter(func):
	_filters[func.__name__] = func
	return func

def create_render_environment():
	from .jinja_extensions import CanvasJinjaEnvironment
	global _render_environment

	template_dirs = get_path_occurrences('assets', 'templates', dir=True)
	_render_environment = CanvasJinjaEnvironment(
		template_dirs, 
		_extensions,
		_filters, 
		_helpers
	)

@export
def render_template(template_path, params=dict(), minify=True):
	template = _render_environment.get_template(template_path)
	
	params['__secrets__'] = dict()
	rendered = template.render(params)
	
	if minify:
		rendered = minify_html(rendered, remove_all_empty_space=True)
	return rendered

from . import default_additions
