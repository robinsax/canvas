#	coding utf-8
'''
Markdown rendering and output caching.
'''

import os

from markdown import markdown as render_markdown

from ...exceptions import MarkdownNotFound
from ...utils import register
from ..plugins import get_path_occurrences
from .templates import markup
from ... import config

@register.template_filter
def markdown(markdown, return_markup=True):
	'''
	Render a string as markdown.

	Available as a template filter.

	:markdown The string to render as markdown.
	:return_markup Whether or not the output should
		be escaped when rendered in Jinja.
	'''
	rendered = render_markdown(markdown)
	if return_markup:
		return markup(rendered)

	return rendered

_markdown_cache = {}
@register.template_helper
def markdown_file(filename, return_markup=True):
	'''
	Load and render a file as markdown.

	Available as a template global.

	:filename The name of the markdown file to render,
		from `/markdown`.
	:return_markup Whether or not the output should
		be escaped when rendered in Jinja.
	'''
	#	Check cache.
	if filename in _markdown_cache:
		if return_markup:
			return markup( _markdown_cache[filename])
		return _markdown_cache[filename]

	#	Get file occurrences.
	paths = get_path_occurrences(os.path.join('assets', 'markdown', filename), filter=os.path.isfile)
	#	Assert an instance exists.
	if len(paths) == 0:
		raise MarkdownNotFound(filename)
	
	#	Load and render.
	with open(paths[-1], 'r') as f:
		rendered = render_markdown(f.read())

	if not config['debug']:
		#	Don't cache in debug mode.
		_markdown_cache[filename] = rendered
	
	if return_markup:
		return markup(rendered)
	return rendered
