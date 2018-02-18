#	coding utf-8
'''
The command-line invocation handler.

canvas should be invoked from the command-line with a *mode* specified. The
invocation syntax is:
```bash
python3.6 -m canvas --<mode> <mode parameters>
```

In the canvas core, the available modes are:
* __serve__, to launch the development server.
* __run_tests__, to run unit test suites.
* __build_docs__, to build the code documentation Markdown.
* __create_plugin__, to create a plugin from the basic template.
* __use_plugins__, to configure set the list of activated plugins in 
	configuration.
* __set_plugin_dir__, to set the plugin directory.
'''

import os
import sys

#	Register the current working directory to allow the `canvas` package to be 
#	imported.
sys.path.insert(0, '.')

from canvas.utils.registration import get_registered
from canvas import launch

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

	#	Return non-zero.
	sys.exit(1)

try:
	mode = sys.argv[1][2:]
except:
	#	Invalid mode argument.
	usage_failure()

#	Search launch mode handlers.
for mode_obj in launch_modes:
	if mode_obj.mode == mode:
		#	This is an applicable handler, invoke it.
		if not mode_obj.launch(sys.argv[2:]):
			#	The handler didn't understand the provided parameters, provide 
			#	them.
			usage_failure()
		#	Success.
		sys.exit(0)

#	An unknown mode was specified.
usage_failure()
