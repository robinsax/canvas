# coding: utf-8
'''
This package handles asset preparation and retrieval. It manages an in-memory 
cache which is kept up-to-date with the filesystem, and implicitly handles the
processing of JSX and LESS assets.
'''

import os

from time import time
from datetime import datetime
from mimetypes import guess_type

from ...utils import logger
from ...configuration import config
from ..plugins import get_path
from .directives import directive, apply_directives
from .processor import transpile_jsx, compile_less
from .palettes import Palette, get_palette

#	Create a logger.
log = logger(__name__)

#	Define the file extension map used to lookup non-existant assets as their
#	unprocessed versions. 
_processed_asset_sources = dict(js='jsx', css='less')
#	Define the asset cache.
_asset_cache = dict()

#	TODO: Golf path lookup.

class Asset:
	'''
	The class representing a in-memory file system asset used internally by 
	this package for cache management.
	'''

	def __init__(self, path=None):
		'''
		Create (but don't load) a new `Asset`. As a precondition, the file at
		`path` must exist.
		::path The path to the asset's file as exposed within the `/assets` 
			realm.
		'''
		self.path = path
		self.load_time = self.data = self.mimetype = None
	
	@property
	def mtime(self):
		'''The modified time of this asset in the file system.'''
		return datetime.utcfromtimestamp(os.path.getmtime(get_path(self.path)))

	def load(self):
		'''Load this asset from the filesystem.'''
		full_path = get_path(self.path)
		if full_path:
			#	Load from the filesystem.
			self.mimetype, enc = guess_type(self.path)
			with open(full_path, 'rb') as asset_file:
				self.data = asset_file.read()
		else:
			#	The file has been deleted.
			self.data = self.mimetype = None
		
		#	Update load time.
		self.load_time = datetime.now()

	def update(self):
		'''Re-load this asset if it has been modified on the filesystem.'''
		if self.load_time < self.mtime:
			self.load()

class ProcessedAsset(Asset):
	'''A JSX or LESS asset that requires processing when loaded.'''

	def __init__(self, root_path, ext):
		'''
		Create (but don't load and process) a new `ProcessedAsset`.
		::root_path The path to the asset's primary module (the to be processed
			version) as exposed within the `/assets` realm.
		::ext The desired file extension after processing.
		'''
		super().__init__()
		self.paths, self.ext = [root_path], ext
		self.mimetype = guess_type('.'.join(('a', ext)))[0]
		#	Define the referenced name of this asset as a module.
		realm_end_i = len(config.route_prefixes.assets) + 1
		self.module = root_path[realm_end_i:-(len(ext) + 2)].replace('/', '.')
		self.source = None

	@property
	def mtime(self):
		'''
		Return the lastest modified time on the filesystem of one of this
		assets component files.
		'''
		return datetime.utcfromtimestamp(
			max(os.path.getmtime(get_path(path)) for path in self.paths)
		)

	def load(self):
		'''Load and process this asset.'''
		#	Load the primary module.
		root_full_path = get_path(self.paths[0])
		with open(root_full_path, 'r') as root_source_file:
			self.source = root_source_file.read()
		
		#	Apply directives.
		apply_directives(self)

		#	Process appropiately.
		if self.ext == 'js':
			self.data = transpile_jsx(self.source)
		elif self.ext == 'css':
			self.data = compile_less(self.source)
		else:
			raise AssetError('Invalid target extension for a processed asset:'
					' %s'%self.ext)
		
		#	Update load time.
		self.load_time = datetime.now()

def new_asset(path):
	'''
	Create a new asset given `path` exposed within the `/assets` realm, or
	return `None`.
	'''
	path, asset = os.path.join('assets', path), None

	full_path = get_path(path)
	if full_path:
		#	This is a basic asset type.
		asset = Asset(path)
	else:
		#	Check for a corresponding processable asset.
		ext = path.split('.')[-1]
		if ext in _processed_asset_sources:
			path = path.replace(ext, _processed_asset_sources[ext])
			processable_path = get_path(path)
			if processable_path:
				asset = ProcessedAsset(path, ext)
	
	if asset:
		#	If an asset was found, perform the initial load.
		asset.load()
	return asset

def get_asset(route):
	'''
	Retrieve an asset given `route` as exposed within the configured asset realm, or
	return `None`.
	'''
	route = route[1:]

	start_time = time()
	if route in _asset_cache:
		asset = _asset_cache[route]
		if asset:
			#	Ensure the asset is filesystem-synced, if it exists.
			asset.update()
	else:
		#	Create and cache a new asset.
		asset = _asset_cache[route] = new_asset(route)
	
	if asset:
		log.debug('Retrieved %s in %.3f', route, time() - start_time)
	return asset
