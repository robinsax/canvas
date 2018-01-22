#	coding utf-8
'''
canvas initialization and namespace generation.
'''

__version__ = '0.0.1'

import os
import logging
import werkzeug as wz

#	TODO: Populate
__all__ = []

#	An alias for the CANVAS_HOME environment variable
#	that controls the base path used by asset and module 
#	loaders. Usually nessesary when running as a service
# 	in Windows environments. Assumed to be the current 
#	working directory when not present.
CANVAS_HOME = os.environ.get('CANVAS_HOME', '')

#	Populate namespace with exceptions and utilities.
from .exceptions import *
from .utils import *

#	Load configuration and create the root configuration
#	storage object, `config`.
from . import configuration
config = configuration.load()

#	Create the root logger.
log = logger()
log.info(f'Initializing...')

#	We don't import the `core.plugins` object as it will 
#	override the canvas.plugins psuedo-module through
#	which loaded plugins are accessed.
from .core.plugins import load_all_plugins

#	Allow plugins to update configuration.
config = configuration.update_from_plugins(config)

#	`canvas.core` and `canvas.launch` only export a subset
#	of their contents through `__all__`, import those to
#	the root namespace.
from .core import *
from .launch import *

#	Import the model and controllers packages for
#	initialization.
from . import model, controllers

#	Load all plugins. Has the side effect of populating
#	the `canvas.plugins` namespace.
load_all_plugins()

#	Invoke pre-initialization callbacks. These should be used 
#	to set up the context for initialization, and can only 
#	assume the core to be initialized.
call_registered('pre_init')

#	Populate the `canvas.model` and `canvas.controllers` 
#	namespaces with all registered models, enums, and controllers.
#	This allows plugins to have have `model` and `controllers`
#	modules or packages without complicating their imports.
place_registered_on('canvas.model', 'model')
place_registered_on('canvas.model', 'enum')
place_registered_on('canvas.controllers', 'controller')

#	Create all singleton objects and perform database
#	initialization.
model.create_everything()
controllers.create_everything()

#	Invoke initialization callbacks.
call_registered('init')

#	Invoke post-initialization callbacks. These can assume
#	the execution context to be identical to that of 
#	a request handling.
call_registered('post_init')

log.info('Initialized')

#	Populate the namespace with the application to be
#	exported to the WSGI server.
application = core.handle_request
