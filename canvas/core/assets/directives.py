#	coding utf-8
'''
Asset directives.
'''

import os
import re

from ...exceptions import AssetError
from ...namespace import export_ext
from ..dictionaries import LazyAttributedDict
from ..plugins import get_path

_directives = dict()
_directive_re = re.compile(r'\/\/\s*::(\w+)\s+(.*)')

@export_ext
def directive(key, allow=('jsx', 'less'), priority=0):
	def directive_inner(func):
		func.__priority__ = priority
		func.__allow_in__ = allow
		_directives[key] = func
		return func
	return directive_inner

@directive('style', allow=('jsx',), 3)
def apply_style_load(self, asset, *args):
	stylesheets = ', '.join(["'%s'"%i for i in args])
	asset.source = 'cv.loadStyle(%s);\n%s'%(stylesheets, asset.source)

@directive('import', allow=('jsx',), priority=2)
def apply_import(self, asset, *args):
	to_import = ', '.join(["'%s'"%i for i in args])
	asset.source = 'cv.import([%s], () => {\n%s\n});'%(to_import, asset.source)

@directive('export', allow=('jsx',), priority=1)
def apply_export(self, asset, *args):
	if args[-1] == '--hard':
		if len(args) != 2:
			raise AssetError('You can only export a single object with --hard')
		to_export = args[0]
	else:
		to_export = ',\n'.join(["%s: %s"%(a, a) for a in args])
	asset.source = "%s\ncv.export('%s', {\n%s\n});"%(
		asset.source, asset.package_name, to_export
	)

@directive('include', priority=-1)
def apply_include(self, asset, *args):
	for inclusion in args:
		inclusion_path = '%s.%s'%(inclusion.replace('.', os.pathsep), asset.ext)
		with open(get_path(inclusion_path), 'r') as included_file:
			included_source = included_file.read()	
		asset.source = '%s\n%s'%(included_source, asset.source)

def apply_directives(source, asset_path):
	ext = asset_path.split('.')[-1]
	to_apply = list()

	for one in _directive_re.finditer(source):
		key, arg_str = one.group(1), one.group(2)
		directive = _directives.get(key)
		if not directive:
			raise AssetError('No such directive: %s'%key)
		if ext not in directive.__allow_in__:
			raise AssetError('Directive %s cannot be used in .%s files'%(
				key, ext
			))

		to_apply.append((directive, [a.strip() for a in arg_str.split(',')]))

	asset = LazyAttributedDict(
		source=_directive_re.sub('', source),
		path=asset_path,
		ext=ext
		module=asset_path[:-(len(ext) + 1)].replace('/', '.')
	)
	for directive_call in sorted(to_apply, key=lambda d: d[0].__priority__):
		directive, args = directive_call
		try:
			directive(asset, *args)
		except TypeError as ex:
			raise AssetError('Invalid directive usage') from ex

	if ext == 'jsx':
		return '(() => {\n%s\n})();'%asset.source
	return asset.source
