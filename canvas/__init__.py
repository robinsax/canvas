#	coding utf-8
'''
canvas initialization and namespace generation.
'''

__version__ = '0.0.1'

import os
import sys
import pprint
import inspect

#	Declare documentation targets.
__documented__ = [
	'canvas',
	'canvas.model',
	'canvas.controllers'
]

#   Declare exports.
__all__ = [
	#	Core.
	'asset_url',
	'create_json',
	'redirect_to',
	'get_thread_context',
	'flash_message',
	#	Assets subpackage.
	'render_template',
	#	Utilities.
	#	Functions.
	'format_traceback',
	'logger',
	#	Subpackage functions - registration.
	'register',
	'callback',
	'get_registered',
	'get_registered_by_name',
	'call_registered',
	'place_registered_on',
	#	Subpackage functions - template_utils.
	'markup',
	'markdown',
	'uri_encode',
	'json',
	#	Classes.
	'WrappedDict',
	#   Exceptions.
	#	Special exceptions.
	'_Redirect',
	'ValidationErrors',
	#	HTTP exceptions.
	'HTTPException',
	'UnsupportedMethod',
	'BadRequest',
	'Unprocessable',
	'RequestParamError',
	'UnknownAction',
	'NotFound',
	#	Other exceptions.
	'TemplateNotFound',
	'ColumnDefinitionError',
	'MacroParameterError',
	'MarkdownNotFound',
	'PluginConfigError',
	'ConfigKeyError',
	'HeaderKeyError',
	'APIRouteDefinitionError',
	'TemplateOverlayError',
	'UnsupportedEnforcementMethod',
	'InvalidSchema',
	'InvalidQuery',
	'UnadaptedType',
	'Unrecognized'
]

#	Retrieve an absolute path to the canvas root directory.
CANVAS_HOME = os.path.abspath(
	os.path.dirname(
		os.path.dirname(inspect.getfile(sys.modules[__name__]))
	)
)

#	Populate namespace with exceptions and utilities.
from .exceptions import *
from .utils import *

#	Load configuration and create the root configuration storage object.
from . import configuration
config = configuration.load()

#	Create the root logger.
log = logger()
log.info(f'Initializing...')

#	Carefully import components of the `core.plugins` module to perserve the 
#	`canvas.plugins` psuedo-module which loaded plugins are accessed.
from .core.plugins import load_all_plugins
from .core.plugins import *

#	Update the configuration object with plugin configurations and wrap it for
#	better key error readback.
config = configuration.finalize(config)
log.debug(f'Runtime configuration: {pprint.pformat(config)}')

#	`canvas.core` and `canvas.launch` only export a subset of their contents 
#	through `__all__`, import those into the `canvas` namespace.
from .core import *
from .launch import *

#	Import the model and controllers packages for initialization.
from . import model, controllers

#	Load all plugins. Has the side effect of populating the `canvas.plugins` 
#	namespace.
load_all_plugins()

#	Invoke pre-initialization callbacks. These are used to prepare for 
#	initialization, and can only assume the core to be initialized.
call_registered('pre_init')

#	Populate the `canvas.model` and `canvas.controllers` namespaces with all 
#	registered models, enums, and controllers. This simplifies plugin packaging
#	by allowing them to have `model` and `controllers` modules without confict,
#	since they can access the contents through the core instances of those
#	namespaces.
place_registered_on('canvas.model', 'model')
place_registered_on('canvas.model', 'enum')
place_registered_on('canvas.controllers', 'controller')

#	Initialize the `model` and `controllers` packages.
model.create_everything()
controllers.create_everything()

#	Invoke initialization callbacks.
call_registered('init')

#	Invoke post-initialization callbacks. These can assume that initialization
#	is completed. 
call_registered('post_init')

log.info(f'canvas {__version__} initialized')

#	Canonically provide the WSGI application.
application = core.handle_request
