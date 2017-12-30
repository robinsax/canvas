#	coding utf-8
'''
Client asset retrieval manager handling
* Caching
* Jinja rendering
* Less compilation
'''

import os
import re
import logging

from io import StringIO

from lesscpy.exceptions import CompilationError
from lesscpy import compile as lessc

from ...exceptions import TemplateNotFound
from ..plugins import get_path_occurrences
from .templates import render_template
from ... import config

log = logging.getLogger(__name__)

_asset_cache = {}
def get_client_asset(path, _recall=False):
	'''
	Return the given asset
	(i.e. a static asset, rendered asset, or None to 404)
	'''
	if path in _asset_cache:
		#	That was easy
		return _asset_cache[path]

	try:
		#	Templates get priority
		asset = render_template(os.path.join('client', path), response=False)
	except TemplateNotFound:
		#	Check for non-template version
		occurrences = get_path_occurrences(os.path.join('assets', 'client', path))
		if len(occurrences) == 0:
			if path.endswith('.css'):
				#	Check for less file, and cache it's .css version
				asset = get_client_asset(path.replace('.css', '.less'), _recall=True)
				if not config['debug']:
					_asset_cache[path] = asset
				return asset
			#	That's a 404
			return None
		with open(occurrences[-1], 'rb') as f:
			asset = f.read()

	if path.endswith('.less') and _recall:
		#	Compile less since it was requested as .css
		try:
			asset = lessc(StringIO(asset), minify=not config['debug'])
		except CompilationError as e:
			#	Try to get the error line since templating makes
			#	line number meaningless
			try:
				line_match = re.search('line: ([0-9]+)', str(e))
				line = asset.split('\n')[int(line_match.group(1))]
				#	TODO: Insert into traceback
				log.error(f'Less compilation failed on: {line}')
			except:
				#	Fuck
				pass
			raise e

	if not config['debug']:
		#	Don't cache assets when debugging
		_asset_cache[path] = asset
	return asset
