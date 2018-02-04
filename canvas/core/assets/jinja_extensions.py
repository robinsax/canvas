#	coding utf-8
'''
Plugin-depth aware Jinja environment and tag additions.
'''

import os
import re

from jinja2.loaders import BaseLoader
from jinja2.nodes import Const, Extends, Include
from jinja2.ext import Extension
from jinja2 import Environment, select_autoescape

from ...exceptions import (
	TemplateNotFound, 
	TemplateOverlayError
)
from ...utils import logger
from ...utils.registration import (
	get_registered, 
	get_registered_by_name
)
from ... import config

#	Create a logger.
log = logger()

class DeepFileSystemLoader(BaseLoader):
	'''
	A Jinja template loader with multiple-occurance awareness.
	'''

	def __init__(self, base_paths):
		'''
		Create a new instance that searches for templates in each of 
		`base_paths`.
		'''
		self.base_paths = list(reversed(base_paths))

		#	The cached path mapping.
		self.path_map = {}

	def get_source(self, environ, template):
		#	Parse template path to check for depth.
		parts = template.split('?')
		depth = int(parts[1]) if len(parts) > 1 else 0
		template = parts[0]

		#	Get the pure template path.
		if template in self.path_map:
			#	Read cached occurances.
			occurrences = self.path_map[template]
		else:
			#	Find path occurrences.
			occurrences = []

			for path in self.base_paths:
				full = os.path.join(path, template)
				if os.path.exists(full):
					occurrences.append(full)

			#	...and cache.
			self.path_map[template] = occurrences
		
		#	Assert the template exists and depth is valid.
		count = len(occurrences)
		if count == 0:
			raise TemplateNotFound(template)
		if depth >= count:
			raise TemplateOverlayError(f'{template}: nothing to overlay (depth {depth})')
		
		#	Retrieve the absolute path at the approprate depth.
		path = occurrences[depth]

		mod_time = os.path.getmtime(path)

		#	Load file as `utf-8`.
		with open(path, 'rb') as src_f:
			source = src_f.read().decode('utf-8')
		
		#	Return.
		return source, path, lambda: mod_time == os.path.getmtime(path)

class ExtendsAlias(Extension):
	'''
	An `ABC` of a fixed-destination `{% extends %}` tag.
	'''
	extension = None

	def parse(self, parser):
		node = Extends(next(parser.stream).lineno)
		node.template = Const(self.__class__.extension)
		return node

class PageTag(ExtendsAlias):
	'''
	The `{% page %}` extends tag alias.
	'''
	tags = {'page'}
	extension = os.path.join('pages', 'base.html')

class ComponentTag(ExtendsAlias):
	'''
	The `{% component %}` extends tag alias.
	'''
	tags = {'component'}
	extension = os.path.join('components', 'base.html')

class OverlayTag(Extension):
	'''
	The `{% overlays %}` tag causes inheritance from a template of the same 
	name at a lower depth. 
	'''
	tags = {'overlays'}

	def __init__(self, environ):
		super().__init__(environ)
		#	Get a reference to the `DeepFileSystemLoader`s path map.
		self.path_map = environ.loader.path_map

	def parse(self, parser):
		#	Get the name of the current template.
		template_path = parser.filename

		#	Create an extends node.
		node = Extends(next(parser.stream).lineno)

		#	Find the next depth.
		overridden_template = None
		#	TODO: Figure out why this works and comment it
		rel_path = re.sub(f'.*?templates{re.escape(os.path.sep)}', '', template_path)
		for i, abs_path in enumerate(self.path_map[rel_path]):
			if abs_path == template_path:
				overridden_template = Const(f'{rel_path}?{i + 1}')

		#	Assert we haven't reached below the bottom.
		if overridden_template is None:
			raise TemplateOverlayError(f'{template_path}: nothing to overlay')

		#	Assign the path to the node and return.
		node.template = overridden_template
		return node

class CanvasJinjaEnvironment(Environment):
	'''
	The Jinja render environment used by canvas.
	'''

	def __init__(self, target_paths):
		self.target_paths = target_paths
		
		#	Collect extensions list.
		extensions =  [
			OverlayTag,
			PageTag,
			ComponentTag
		]
		extensions.extend(get_registered('jinja_extension'))

		super().__init__(**{
			'loader': DeepFileSystemLoader(target_paths),
			'autoescape': select_autoescape(['html', 'xml']),
			'extensions': extensions
		})
		
		#	Add all registered template filters.
		self.filters.update(get_registered_by_name('template_filter'))

		#	Add all registered template globals, template helpers, and the 
		#	configuration storage object.
		self.globals.update(**{
			**get_registered_by_name('template_global'),
			**{
				'config': config,
				'h': get_registered_by_name('template_helper')
			}
		})

		log.debug(f'Created {repr(self)}')

	def __repr__(self):
		return f'<{self.__class__.__name__}: {str(self.target_paths)}>'
