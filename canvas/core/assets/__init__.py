#	coding utf-8
'''
Asset management.
'''

import re

from io import StringIO

from lesscpy.exceptions import CompilationError
from lesscpy import compile as lessc

from ...utils import logger
from ...utils.registration import callback
from .templates import *

log = logger()

#	TODO: Populate appropriately.
__all__ = [
	'render_template',
	'compile_less'
]

_header = None
@callback.init
def render_header():
	'''
	Renders the less file common definitions, which make
	configured style properties available in all rendered
	less files.
	'''
	global _header
	_header = render_template('snippets/less_common.less')
del render_header

def compile_less(source):
	'''
	Compile less source with the common definitions prepended.
	'''
	#	Prepend the common definitions.
	source = _header + source
	#	Render the less.
	try:
		return lessc(StringIO(source), minify=not config['debug'])
	except CompilationError as e:
		#	Try to get the error line since definition insertion 
		#	makes line number meaningless.
		try:
			line_match = re.search('line: ([0-9]+)', str(e))
			line = source.split('\n')[int(line_match.group(1))]
			#	TODO: Insert into traceback
			log.error(f'Less compilation failed on: {line}')
		except:
			#	Fuck.
			pass
		raise e

#	The client submodule imports compile less.
from .client import *
