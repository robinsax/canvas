#	coding utf-8
'''
Less rendering and palette management.
'''

import io
import re

from lesscpy.exceptions import CompilationError
from lesscpy import compile as lessc

from ..exceptions import (
	ConfigurationError,
	AssetError
)
from ..namespace import export
from ..configuration import config
from ..utils import logger
from .plugins import get_path_occurrences

log = logger(__name__)

_less_header = None

def load_palette():
	global _less_header
	palette = config.customization.palette

	occurrences = get_path_occurrences('assets', 'palettes', '%s.palette'%palette)
	if len(occurrences) == 0:
		raise ConfigurationError('No palette found: %s'%palette)

	with open(occurrences[-1], 'r') as palette_file:
		palette_data = palette_file.read()
	log.debug('Loaded palette: %s', occurrences[-1])

	declarations = []
	for match in re.finditer(r'(.*?)\s+->\s+(.*?)\r*(?:\n|$|&)', palette_data):
		value, labels = match.group(1), match.group(2)
		for label in [l.strip() for l in labels.split(',')]:
			declarations.append('@%s: %s;'%(label, value))
	_less_header = '\n'.join(declarations) + '\n'

@export
def compile_less(source):
	source = _less_header + source

	try:
		return lessc(io.StringIO(source), minify=not config.development.debug)
	except CompilationError as ex:
		raise AssetError(str(ex)) from None