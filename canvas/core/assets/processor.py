# coding: utf-8
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
	'''
	Invoke `processor.js` to processes `source` as type `which` ('jsx' or 
	'less').
	'''
	#	Create the command line.
	cmdline = ' '.join(('node', _script_path, which))
	log.debug('Compiling asset: %s', cmdline)
	
	#	Synchronously run the processor script.
	proc_proc = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE)
	stdout, stderr = proc_proc.communicate(input=source.encode('utf-8'))

	#	Assert the processing was successful.
	if proc_proc.returncode != 0:
		raise AssetError('Asset processing failed with code %s:\n%s\n'%(
			proc_proc.returncode, stderr.decode('utf-8')
		))
	
	return stdout.decode('utf-8')

def transpile_jsx(source):
	'''Transpile JSX into ES5 JavaScript.'''
	return process(source, 'jsx')

def compile_less(source, palette='default'):
	'''
	Compile LESS into CSS.
	::palette The name of the palette to use.
	'''
	source = '\n'.join((get_palette(palette).as_less(), source))
	return process(source, 'less')
