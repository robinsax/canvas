#	coding utf-8
'''
Configure canvas for a plugin Travis build.

Must be invoked from root directory.
'''

import re
import sys
import json

with open('settings.json') as f:
	config = json.load(f)

config['plugins']['active'].append(sys.argv[1])
config['plugins']['directory'] = '..'
config_str = re.sub('\n    ', '\n\t', json.dumps(config, indent=4))

with open('settings.json', 'w') as f:
	f.write(config_str)
