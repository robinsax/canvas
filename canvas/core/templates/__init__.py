#	coding utf-8
'''
Jinja extentions and template actualization.
'''

from htmlmin import minify as minify_html

from ...namespace import export, export_ext
from ...utils import logger
from ...configuration import config
from ..plugins import get_path_occurrences

log = logger(__name__)

_extensions = ['jinja2.ext.do']
_globals = dict()
_helpers = dict()
_filters = dict()
_render_environment = None

@export_ext
def jinja_extension(extension):
	_extensions.append(extension)
	return extension

@export
def template_global(item, name=None):
	if name is None:
		name = item.__name__
	_globals[name] = item
	return item

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
	log.debug('Template search paths: %s'%template_dirs)
	_render_environment = CanvasJinjaEnvironment(
		template_dirs,
		_extensions,
		_globals,
		_filters, 
		_helpers
	)

@export
def render_template(template_path, params=dict(), minify=True):
	template = _render_environment.get_template(template_path)
	
	params.update({
		'global_dependencies': ['lib/toolkit.min.js', 'canvas.js', 'canvas.css'],
		'icon_stylesheet': 'font-awesome.min.css'
	})
	rendered = template.render(params)
	
	if minify:
		rendered = minify_html(rendered, remove_all_empty_space=True)
	return rendered

from . import default_additions
