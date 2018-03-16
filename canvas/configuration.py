#	coding utf-8
'''
Configuration storage and management.
'''

import os
import json

from .namespace import export
from .core.dictionaries import Configuration
from . import HOME

config = Configuration()
export('config')(config)

def load_config():
	with open(os.path.join(HOME, 'settings.json'), 'r') as f:
		local_config = json.load(f)

	for key, value in local_config.items():
		config[key] = value
