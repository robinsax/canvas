#	coding utf-8
'''
The interface with `./processor.js`, which contains the asset
processor invocation logic.
'''

import os

from subprocess import Popen, PIPE

from ...exceptions import AssetError
from ...configuration import config
from ...utils import logger
from ... import __home__
from .palettes import get_palette

log = logger(__name__)

#	The path of the processor script.
_script_path = os.path.join(*(
	__home__, 'canvas', 'core', 'assets', 'processor.js'
))

def process(source, which):
	#	Create the command line.
	cmdline = ' '.join(('node', _script_path, which))
	log.debug('Compiling asset: %s', cmdline)
	
	#	Synchronously run the processor script.
	proc_proc = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	stdout, stderr = proc_proc.communicate()

	#	Assert the processing was successful.
	if compile_proc.returncode != 0:
		raise AssetError('%s compilation failed with code %s:\n%s\n'%(
			compile_proc.returncode, stderr
		))

	#	Return the result.
	return stdout

def transpile_jsx(source):
	'''Transpile JSX into ES5 JavaScript.'''
	return process(source, 'jsx')

def compile_less(source, palette='default'):
	'''
	Compile LESS into CSS.
	::palette The name of the palette to use.
	'''
	source = '\n'.join(source, get_palette(palette))
	return process(source, 'less')
