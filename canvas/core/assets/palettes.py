# coding: utf-8
'''
`Palette`s are style definition files comprised of font file inclusions and a
one to many map of style keys to values. less files are compiled as a function 
of a palette. Palette files are stored in the `assets\palettes` directory and 
have a `.palette` extension.

This module is responsible for the load, parsing, and translation of palette 
files.
'''

import os
import re

from ...utils import logger
from ...namespace import export_ext
from ..plugins import get_path

log = logger(__name__)

#	The global palette storage mapping names to Palette instances.
_palettes = dict()

@export_ext
def get_palette(name):
	'''Retrieve the `Palette` called `name`, or `None` if none exists.'''
	#	Check for a loaded version, returning it if it exists.
	loaded = _palettes.get(name)
	if loaded:
		#	Maybe reload the Palette and return it.
		loaded.update()
		return loaded
	
	#	Retrieve the highest priority path to the palette.
	path = get_path('assets', 'palettes', '%s.palette'%name)
	if not path:
		#	No path exists; return the default Palette.
		log.debug('No such palette %s; fallback to default', name)
		return get_palette('default')
	
	#	Load, save, and return a new Palette instance.
	return _palettes[name] = Palette(path)

class Palette:
	'''A representation of a parsed `.palette` file.'''

	def __init__(self, path):
		'''
		Create and load a new `Palette`. `path` must be an existant `.palette`
		file.
		::path The path to the `.palette` file.
		'''
		self.path = path
		self.fonts = self.styles = self.load_time = None

		#	Perform initial load.
		self.load()

	def load(self):
		'''Load and parse the source file of this `Palette`.'''
		#	Read the source file.
		with open(self.path, 'r') as palette_file:
			to_parse = palette_file.read()
		
		#	Parse the font definitions.
		self.fonts = dict()
		for font_decl in re.finditer(r'::font\s+(.*?)\s+(.*)', to_parse):
			self.fonts[font_decl.group(1)] = font_decl.group(2)

		#	Parse the style map.
		self.styles = dict()
		for style_mapping in re.finditer(r'(.*?)\s+->\s+(.*?)\r*(?:\n|$|&)', to_parse):
			style = style_mapping.group(1)

			for key in [l.strip() for l in style_mapping.group(2).split(',')]:
				self.styles[key] = style

		#	Update the load time.
		self.load_time = os.path.getmtime(self.path)

	def update(self):
		'''Reload this palette if it has changed since it was last loaded.'''
		if os.path.getmtime(self.path) > self.load_time:
			self.load()

	def as_less(self):
		'''Return a string containing this `Palette`s less representation.'''
		lines = []

		#	Create font faces.
		for name, filename in self.fonts.items():
			lines.append("@font-face { font-family: %s; src: url('/assets/fonts/%s'); }"\
					%(name, filename))
		
		#	Define variable from style map.
		for key, style in self.styles.items():
			lines.append('@%s: %s;'%(key, style))

		return '\n'.join(lines)
