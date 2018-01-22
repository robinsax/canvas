#	coding utf-8
'''
The intended command line invocation entry point.
'''

import os
import sys

#	Register the current working directory to
#	allow the canvas package to be imported.
sys.path.insert(0, '.')

from canvas.utils.registration import get_registered

#	Instantiate launch mode handlers.
launch_modes = [cls() for cls in get_registered('launch_mode')]

def usage_failure():
	'''
	Display usage information and exit as failed.
	'''
	#	Create string representation of usage options.
	modes_str = '\n\t'.join([f'--{m.mode} {m.arg_fmt}' for m in launch_modes])

	#	Present.
	print(f'Usage: python3.6 canvas [\n\t{modes_str}\n]')

	#	Failure; unable to perform an operation.
	sys.exit(1)

try:
	mode = sys.argv[1][2:]
except:
	#	Invalid mode argument; unable to perform an operation.
	usage_failure()

#	Iterate launch mode handlers.
for mode_obj in launch_modes:
	if mode_obj.mode == mode:
		#	Applicable handler found, invoke and exit 
		#	appropriately.
		sys.exit(0 if mode_obj.handle(sys.argv[1:]) else 1)

#	Unknown mode; unable to perform an operation.
usage_failure()
