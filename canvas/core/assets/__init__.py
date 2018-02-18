#	coding utf-8
'''
Asset management, retrieval, and rendering.
'''

import re

from io import StringIO

from lesscpy.exceptions import CompilationError
from lesscpy import compile as lessc

from ...utils.registration import callback
from .jinja_extensions import *
from .templates import *

__all__ = [
	#	Common.
	'CanvasJinjaEnvironment',
	'DeepFileSystemLoader',
	'ExtendsAlias',
	'get_asset',
	#	Jinja.
	'render_template',
	#	Less.
	'compile_less'
]

#	The common `less` definitions storage object.
_less_defns = None

@callback.init
def render_common_less_defns():
	'''
	Render the common `less` variable definitions to make configured style 
	properties available in all rendered `less` files.
	'''
	global _less_defns
	_less_defns = render_template('snippets/less_definitions.jinja')
del render_common_less_defns

def compile_less(source):
	'''
	Compile `less` source with the common definitions prepended.

	:source A string containing the source `less` to be compiled.
	'''
	#	Prepend the common definitions.
	source = _less_defns + source

	#	Compile.
	try:
		return lessc(StringIO(source), minify=not config['debug'])
	except CompilationError as ex:
		#	Try to get the error line since definition insertion makes line 
		#	number less useful.
		try:
			line_no = int(re.search('line: ([0-9]+)', str(e)).group(1))
			line = source.split('\n')[line_no]
			#	TODO: Insert into traceback.
			ex = CompilationError(f'Less compilation failed: {line} (line {line_no})')
		except:
			#	Fuck.
			pass
		raise ex

#	The `client` submodule imports `compile_less()`.
from .client import *
