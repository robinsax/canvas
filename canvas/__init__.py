#	coding utf-8
'''
TODO
'''

__version__ = '0.0.1'

#	TODO
__all__ = []

import os
import logging
import werkzeug as wz

if 'CANVAS_HOME' not in os.environ:
	os.environ['CANVAS_HOME'] = '.'
CANVAS_HOME = os.environ['CANVAS_HOME']

#	Populate namespace with exceptions and utils
from .exceptions import *
from .utils import *

#	Load configuration
from . import configuration
config = configuration.load()

log = logger()
log.debug(f'Initializing... (CANVAS_HOME at {CANVAS_HOME})')

#	Load plugins and update config. with them
from .core import plugins
config = configuration.update_from_plugins(config)

from .core import *
from . import model, controllers

plugins.load_all()

call_registered('callback:pre_init')

#	Place registered models and controllers to
#	make plugin packaging easier
place_registered_on('canvas.model', 'model')
place_registered_on('canvas.controllers', 'controller')

#	Instantiate singleton everything
model.create_tables()
controllers.create_everything()

#	Call initialization functions
call_registered('callback:init')
call_registered('callback:post_init')

log.info('Initialized')

application = core.handle_request
