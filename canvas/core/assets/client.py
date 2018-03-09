#	coding utf-8
'''
Client asset rendering and retrieval.
'''

import os

from ...exceptions import TemplateNotFound
from ... import config
from ..plugins import get_path_occurrences
from .templates import render_template
from . import compile_less, transpile_js

#	The asset cache for storing rendered assets.
_asset_cache = {}

def get_asset(path, _recall=False):
	'''
	Return the asset at `path`, or `None` if there isn't one. Besides searching
	the `client` directory, also:

	* Searches `templates/client`, giving assets found here prescedence.
	* Searches for `.less` versions of non-existant `.css` files, compiling and
		returning them if found.
	'''
	if path in _asset_cache:
		#	Retrieve cache entry.
		return _asset_cache[path]
	
	occurrences = get_path_occurrences(os.path.join('assets', 'client', path))
	if len(occurrences) == 0:
		#	No occurences found.

		if path.endswith('.css'):
			#	Check for a `.less` instance of this stylesheet.
			asset = get_asset(path.replace('.css', '.less'), _recall=True)
		else:
			#	No asset found.
			return None
		
		if not config['debug']:
			#	Don't cache assets in debug mode so changes can be 
			#	viewed without server restart. Cache even if `None` to 
			#	avoid re-performing this logic.
			_asset_cache[path] = asset
		return asset
		
	#	Read the asset.
	with open(occurrences[-1], 'rb') as f:
		asset = f.read()

	if _recall:
		if path.endswith('.less'):
			#	Compile the `.less` asset since it was requested as `.css`.
			if not isinstance(asset, str):
				asset = asset.decode()
			asset = compile_less(asset)

	if path.endswith('.js'):
		#	Transpile in case it's ES6.
		asset = transpile_js(asset)
	
	if not config['debug']:
		#	Don't cache assets in debug mode so changes can be viewed without 
		#	server restart.
		_asset_cache[path] = asset
	return asset
