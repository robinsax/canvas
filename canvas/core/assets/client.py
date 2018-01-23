#	coding utf-8
'''
Client asset rendering and retrieval.
'''

import os
import re
import logging

from io import StringIO

from lesscpy.exceptions import CompilationError
from lesscpy import compile as lessc

from ...exceptions import TemplateNotFound
from ...utils import logger
from ..plugins import get_path_occurrences
from .templates import render_template
from ... import config

log = logger()

#	TODO: Refactor to have a get_asset function too.

#	The asset cache for storing rendered assets.
_asset_cache = {}
def get_client_asset(path, _recall=False):
	'''
	Return the asset at `path`, or `None` if there
	isn't one.
	'''
	if path in _asset_cache:
		#	Retrieve cache entry.
		return _asset_cache[path]
	
	try:
		#	Jinja templates have priority.
		asset = render_template(os.path.join('client', path), response=False)
	except TemplateNotFound:
		#	No template for this asset, retrieve non-template
		#	occurences.
		occurrences = get_path_occurrences(os.path.join('assets', 'client', path))
		if len(occurrences) == 0:
			#	No occurences found.
			if path.endswith('.css'):
				#	`.less` files requested as `.css` are returned 
				#	compiled, check for a `.less` instance for 
				#	this asset
				asset = get_client_asset(path.replace('.css', '.less'), _recall=True)

				if not config['debug']:
					#	Don't cache assets in debug mode so changes
					#	can be viewed without server restart. Cache
					#	`None` to avoid re-performing this logic.
					_asset_cache[path] = asset
				return asset
			
			#	No asset found.
			return None
		
		#	Read the asset.
		with open(occurrences[-1], 'rb') as f:
			asset = f.read()

	if path.endswith('.less') and _recall:
		#	Compile the `.less` asset since it was 
		#	requested as css.
		try:
			asset = lessc(StringIO(asset), minify=not config['debug'])
		except CompilationError as e:
			#	Try to get the error line since templating makes
			#	line number meaningless.
			try:
				line_match = re.search('line: ([0-9]+)', str(e))
				line = asset.split('\n')[int(line_match.group(1))]
				#	TODO: Insert into traceback
				log.error(f'Less compilation failed on: {line}')
			except:
				#	Fuck.
				pass
			raise e

	if not config['debug']:
		#	Don't cache assets in debug mode so changes
		#	can be viewed without server restart.
		_asset_cache[path] = asset
	return asset
