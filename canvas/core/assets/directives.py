#	coding utf-8
'''
Asset preprocessor directives are used to make JavaScript dependency and 
stylesheet management easier. They have the following format:

```
//	::<directive> <argument 1>, ..., <argument n>
```

The `directive` decorator can be used to define custom directives.

The default directives are:
* `import x`: A JavaScript dependency declaration.
* `export y`: A declaration of exposed object and functions (by default, a 
	JavaScript asset exposes nothing as it is executed in a closure).
* `style x`: A stylesheet inclusion.
* `include x`: A literal file insertion.
'''

import os
import re

from ...exceptions import AssetError
from ...namespace import export_ext
from ..plugins import get_path

#	The global name to directive function mapping.
_directives = dict()
#	The regular expression used to match directives.
_directive_re = re.compile(r'\/\/\s*::(\w+)\s+(.*)')

@export_ext
def directive(name, allow=('jsx', 'less'), priority=0):
	'''
	Declare the decorated function as being a directive.
	::name The reference name of the directive.
	::allow An iterable of the assets within which this directive is allowed.
	::priority The priority of the directive within the pre-application sort
		Higher priority directives are applied last (at top).
	'''
	def directive_inner(func):
		func.__priority__ = priority
		func.__allow_in__ = allow
		_directives[name] = func
		return func
	return directive_inner

@directive('style', allow=('jsx',), 3)
def apply_style_load(self, asset, *args):
	'''The stylesheet inclusion directive.'''
	stylesheets = ', '.join(["'%s'"%i for i in args])

	asset.source = 'cv.loadStyle(%s);\n%s'%(stylesheets, asset.source)

@directive('import', allow=('jsx',), priority=2)
def apply_import(self, asset, *args):
	'''The depenency declaration directive.'''
	to_import = ', '.join(["'%s'"%i for i in args])

	asset.source = 'cv.import([%s], () => {\n%s\n});'%(to_import, asset.source)

@directive('export', allow=('jsx',), priority=1)
def apply_export(self, asset, *args):
	'''
	The module exposure directive. The `--hard` option specifies that the
	referenced object *is* the object to expose rather than a property of it.
	'''
	if args[-1] == '--hard':
		#	Export the specified object directly.
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
	'''The literal file inclusion directive.'''
	for inclusion in args:
		inclusion_path = '.'.join((
			inclusion.replace('.', os.pathsep), asset.ext
		))
		with open(get_path(inclusion_path), 'r') as included_file:
			included_source = included_file.read()

		asset.paths.append(inclusion_path)
		asset.source = '\n'.join((included_source, asset.source))

def apply_directives(asset):
	'''
	Apply all preprocessor directives of `asset`. This will mutate the asset.
	::asset The `ProcessedAsset` to apply the preprocessor directives of.
	'''
	to_apply = list()

	#	Collect directives.
	for one in _directive_re.finditer(asset.source):
		key, arg_str = one.group(1), one.group(2)
		directive = _directives.get(key)
		
		#	Assert the use is valid.
		if not directive:
			raise AssetError('No such directive: %s'%key)
		if ext not in directive.__allow_in__:
			raise AssetError('Directive %s cannot be used in .%s files'\
					%(key, ext))

		#	Push the directive, argument iterable pair.
		to_apply.append((directive, [a.strip() for a in arg_str.split(',')]))
	
	#	Remove directives from the source.
	asset.source = _directive_re.sub('', asset.source)

	#	Iterate and apply the directives based on priority.
	for directive_call in sorted(to_apply, key=lambda d: d[0].__priority__):
		directive, args = directive_call
		try:
			directive(asset, *args)
		except TypeError as ex:
			#	TODO: Better safety
			raise AssetError('Invalid directive usage') from ex

	if asset.ext == 'js':
		#	Closurize JavaScript.
		asset.source = '(() => {\n%s\n})();'%asset.source
