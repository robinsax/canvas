#	coding utf-8
'''
Default extension, helper, and filter definitions.
'''

import os
import re

from jinja2 import Markup
from jinja2.nodes import Extends, Const
from jinja2.ext import Extension

from ..styles import compile_less
from .jinja_extensions import ExtendsAliasTag
from . import jinja_extension, template_filter, template_helper

@jinja_extension
class PageTag(ExtendsAliasTag):
	tags = ('page',)
	extension = 'base.html'

@jinja_extension
class OverlayTag(Extension):
	tags = ('overlays',)

	def __init__(self, environ):
		super().__init__(environ)
		self.path_map = environ.loader.path_map

	def parse(self, parser):
		template_path = parser.filename

		node = Extends(next(parser.stream).lineno)
		overridden_template = None
		rel_path = re.sub('.*?templates%s'%re.escape(os.path.sep), '', template_path)
		for i, abs_path in enumerate(self.path_map[rel_path]):
			if abs_path == template_path:
				overridden_template = Const('%s?%d'%(rel_path, i + 1))

		if overridden_template is None:
			raise TemplateOverlayError(f'{template_path}: nothing to overlay')
		node.template = overridden_template
		return node

@template_filter
def markup(string):
	return Markup(string)

@template_filter
def normalize_whitespace(string):
	return re.sub(r'\s+', ' ', string).strip()

@template_filter
def less(source, minify=True):
	return markup(compile_less(source, minify=minify))

@template_helper
def asset_url(subroute):
	if not subroute.startswith('/'):
		subroute = '/%s'%subroute
	return '/assets%s'%subroute
