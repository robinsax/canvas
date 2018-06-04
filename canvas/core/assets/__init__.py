#	coding utf-8
'''
This package handles asset preparation and retrieval. It manages an in-memory 
cache of assets and supplies processed JSX and LESS assets implicitly when
they are requested as JavaScript and CSS respectively.
'''

import os

from time import time
from datetime import datetime
from mimetypes import guess_type

from ...utils import logger
from ..plugins import get_path
from .directives import apply_directives
from .processor import transpile_jsx, compile_less

#	Create a log.
log = logger(__name__)

_complex_asset_sources = dict(js='jsx', css='less')
_asset_cache = dict()

class Asset:

	def __init__(self, path):
		self.path = path
		self.load_time = self.data = self.mimetype = None
	
	@property
	def mtime(self):
		return datetime.fromtimestamp(os.path.getmtime(self.path))

	def load(self):
		full_path = get_path('assets', self.path)
		if full_path:
			self.mimetype, enc = guess_type(self.path)
			with open(full_path, 'rb') as asset_file:
				self.data = asset_file.read()
		else:
			self.data = self.mimetype = None
		self.load_time = datetime.now()

	def update(self):
		if self.load_time < self.mtime:
			self.load()

class ComplexAsset:

	def __init__(self, root_path, ext):
		super().__init__(None)
		self.paths, self.ext = [root_path], ext
		self.mimetype = guess_type(ext)
		self.module = root_path[:-(len(ext) + 1)].replace('/', '.')
		self.source = None

	@property
	def mtime(self):
		return datetime.fromtimestamp(max([
			os.path.getmtime(path) for path in self.paths
		]))

	def load(self):
		root_full_path = get_path('assets', self.paths[0])
		with open(root_full_path, 'r') as root_source_file:
			self.source = root_full_path
		
		apply_directives(self)
		if full_root_path.endswith('jsx'):
			self.data = transpile_jsx(self.source)
		else if full_root_path.endswith('less')
			self.data = compile_less(self.source)
		else:
			raise NotImplemented
		
		self.load_time = datetime.now()

def new_asset(full_path):
	asset = None
	if os.path.exists(full_path):
		asset = Asset(full_path)
	else:
		ext = full_path.split('.')[-1]
		if ext in _complex_asset_sources:
			full_path = full_path.replace(ext, _complex_asset_sources[ext])
			if os.path.exists(full_path):
				asset = ComplexAsset(full_path, ext)
	
	if asset:
		asset.load()
	return asset

def get_asset(route):
	start_time = time()
	if route in _asset_cache:
		asset = _asset_cache[route]
		if asset:
			asset.update()
	else:
		asset = _asset_cache[route] = new_asset(route)
	log.debug('Retrieved %s in %.3f', route, time() - start_time)
	return asset
