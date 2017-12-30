#	coding utf-8
'''
Canvas Jinja extensions
'''

import os
import re
import logging

from jinja2 import Environment, select_autoescape
from jinja2.ext import Extension
from jinja2.nodes import Const, Extends, Include
from jinja2.loaders import BaseLoader

from ...exceptions import TemplateNotFound, TemplateOverlayError
from ...utils import get_registered_by_name
from ... import config

log = logging.getLogger(__name__)

class DeepFileSystemLoader(BaseLoader):
	'''
	A Jinja loader that allows the overlay
	tag functionality.
	'''

	def __init__(self, base_paths):
		self.base_paths = list(reversed(base_paths))
		self.path_map = {}

	def get_source(self, environ, template):
		#	Check if depth was specified by `OverlayTag`
		parts = template.split('?')
		depth = int(parts[1]) if len(parts) > 1 else 0
		template = parts[0]
		if template in self.path_map:
			#	Occurrences already found
			occurrences = self.path_map[template]
		else:
			#	Find occurrences
			occurrences = []
			for path in self.base_paths:
				full = os.path.join(path, template)
				if os.path.exists(full):
					occurrences.append(full)
			#	...and cache
			self.path_map[template] = occurrences
		log.debug(f'{template} found at {occurrences} (depth {depth})')
		#	Ensure the template exists and depth is
		#	valid
		count = len(occurrences)
		if count == 0:
			raise TemplateNotFound(template)
		if depth >= count:
			raise TemplateOverlayError(f'{template}: nothing to overlay (depth {depth})')
		path = occurrences[depth]
		mtime = os.path.getmtime(path)
		with open(path, 'rb') as src_f:
			source = src_f.read().decode('utf-8')
		return source, path, lambda: mtime == os.path.getmtime(path)

class ExtendsAlias(Extension):
	extension = None

	def parse(self, parser):
		node = Extends(next(parser.stream).lineno)
		node.template = Const(self.__class__.extension)
		return node

class PageTag(ExtendsAlias):
	'''The `{% page %}` tag'''
	tags = {'page'}
	extension = os.path.join('pages', 'base.html')

class ComponentTag(ExtendsAlias):
	'''The `{% component %}` tag'''
	tags = {'component'}
	extension = os.path.join('components', 'base.html')

class LessTag(Extension):
	'''
	The `{% less %}` tag
	'''
	tags = {'less'}
	
	def parse(self, parser):
		node = Include(Const(os.path.join('snippets', 'less_common.less')), True, False, lineno=next(parser.stream).lineno)
		return node

class OverlayTag(Extension):
	'''
	The `{% overlays %}` tag
	'''
	tags = {'overlays'}

	def __init__(self, environ):
		super().__init__(environ)
		self.path_map = environ.loader.path_map

	def parse(self, parser):
		#	Get currently rendering file path
		template_path = parser.filename

		#	Create extends node to give our
		#	overridden depth file path
		node = Extends(next(parser.stream).lineno)

		#	Find the next depth
		overridden_template = None

		#	TODO: Figure out why this works and comment it
		rel_path = re.sub(f'.*?templates{re.escape(os.path.sep)}', '', template_path)
		for i, abs_path in enumerate(self.path_map[rel_path]):
			if abs_path == template_path:
				overridden_template = Const(f'{rel_path}?{i + 1}')

		if overridden_template is None:
			raise TemplateOverlayError(f'{template_path}: nothing to overlay')

		node.template = overridden_template
		return node

class CanvasJinjaEnvironment(Environment):

	def __init__(self, target_paths):
		super().__init__(**{
			'loader': DeepFileSystemLoader(target_paths),
			'autoescape': select_autoescape(['html', 'xml']),
			'extensions': [
				OverlayTag,
				PageTag,
				ComponentTag,
				LessTag
			]
		})
		
		self.filters.update(get_registered_by_name('template_filter'))
		self.globals.update(**{
			**get_registered_by_name('template_global'),
			**{
				'config': config
			}
		})

		log.debug(f'CanvasJinjaEnvironment: {str(target_paths)}')
