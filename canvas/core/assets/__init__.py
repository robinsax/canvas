#	coding utf-8
'''
Asset management, retrieval, and rendering.
'''

import re
import os
import coffeescript

from io import StringIO
from subprocess import Popen, PIPE

from lesscpy.exceptions import CompilationError
from lesscpy import compile as lessc

from ...exceptions import AssetCompilationError
from ...utils.registration import callback
from ..plugins import get_path_occurrences
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
	#	Less and CoffeeScript.
	'compile_less',
	'compile_coffee'
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
			ex = AssetCompilationError(f'Less compilation failed: {line} (line {line_no})')
		except:
			#	Fuck.
			pass
		raise ex

def compile_coffee(source):
	'''
	Compile CoffeeScript.

	:path The absolute path to the file.
	'''
	if not isinstance(source, str):
		source = source.decode()

	#	Resolve inclusions.
	for include_defn in re.finditer(r'#\s+::include\s+(.+)\s*?\n', source):
		#	Check templates first.
		include_filename = f'{include_defn.group(1).strip()}.coffee'
		try:
			included = render_template(os.path.join(include_filename, path), response=False)
		except TemplateNotFound:
			#	Check non-templates.
			occurences = get_path_occurrences(
				os.path.join('assets', 'client', include_filename)
			)
			if len(occurences) == 0:
				raise AssetCompilationError(f'Invalid include: {include_defn.group(1)}')
			with open(occurences[-1], 'r') as f:
				included = f.read()
		
		source = source.replace(include_defn.group(0), included)

	try:
		compiled = coffeescript.compile(source)
	except BaseException as ex:
		log.warning(source)
		raise ex from None
	
	babel = Popen(f'babel --no-babelrc --presets=es2015', shell=True, stdin=PIPE, stdout=PIPE)
	out, err = babel.communicate(input=compiled.encode('utf-8'))
	if babel.returncode != 0:
		raise AssetCompilationError(err.decode())
	return out

#	The `client` submodule imports `compile_less` and `compile_ts`.
from .client import *
