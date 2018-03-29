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
from ...namespace import export
from ...configuration import config

class DeepLoader(BaseLoader):

	def __init__(self, base_paths):
		self.base_paths = list(reversed(base_paths))
		self.path_map = {}

	def get_source(self, environ, template):
		parts = template.split('?')
		depth = int(parts[1]) if len(parts) > 1 else 0
		template = parts[0]

		if template in self.path_map:
			occurrences = self.path_map[template]
		else:
			occurrences = []

			for path in self.base_paths:
				full = os.path.join(path, template)
				if os.path.exists(full):
					occurrences.append(full)

			self.path_map[template] = occurrences
		
		count = len(occurrences)
		if count == 0:
			raise TemplateNotFound(template)
		if depth >= count:
			raise TemplateOverlayError('%s: nothing to overlay (depth %s)'%(template, depth))

		path = occurrences[depth]
		mod_time = os.path.getmtime(path)
		with open(path, 'rb') as src_f:
			source = src_f.read().decode('utf-8')
		return source, path, lambda: mod_time == os.path.getmtime(path)

@export
class ExtendsAliasTag(Extension):
	extension = None

	def parse(self, parser):
		node = Extends(next(parser.stream).lineno)
		node.template = Const(self.__class__.extension)
		return node

class CanvasJinjaEnvironment(Environment):
	def __init__(self, target_paths, extensions, globs, filters, helpers):
		super().__init__(
			loader=DeepLoader(target_paths),
			autoescape=select_autoescape(['html', 'xml']),
			extensions=extensions
		)
		
		self.target_paths = target_paths
		self.filters.update(filters)

		self.globals.update(globs)
		self.globals.update(
			config=config,
			h=helpers
		)
