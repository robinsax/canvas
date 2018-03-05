#	coding utf-8
'''
canvas is a full stack web application framework designed for minimalism and
extensibility. This package contains the WSGI application that constitutes
its backend.

All of the canvas backend's exposed functionality, aside from its `model` and 
`controller` packages (which are inteded by individual import), is available 
within this namespace. The canonical import is
```python
import canvas as cv
```
'''

__version__ = '0.1'

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

#   Declare the canvas namespace.
__all__ = [
	#	Debugging access.
	'serve',
	#	Core functions.
	'create_json',
	'redirect_to',
	'get_thread_context',
	'flash_message',
	'render_template',
	'asset_url',
	'get_asset',
	'compile_less',
	#	Utilities functions.
	'format_traceback',
	'logger',
	#	Registration and management functions and decorators.
	'register',
	'callback',
	'get_registered',
	'get_registered_by_name',
	'call_registered',
	'place_registered_on',
	#	File management.
	'get_path_occurrences',
	#	Template utilities; included for completeness.
	'markup',
	'markdown',
	'uri_encode',
	'json',
	#	Utility classes.
	'WrappedDict',
	#	JSON interface.
	'serialize_json',
	'deserialize_json',
	'JSONSerializer',
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
	'ServiceUnavailable',
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
	'Unrecognized',
	'AssetCompilationError'
]

#	Compute an absolute path to the canvas root directory, the parent 
#	directory of this package.
CANVAS_HOME = os.path.abspath(
	os.path.dirname(
		os.path.dirname(inspect.getfile(sys.modules[__name__]))
	)
)

#	Import all exported exceptions and utilities. No exported modules in either
#	of these packages can perform immediate imports from this package or any
#	other.
from .exceptions import *
from .utils import *

#	Load the root configuration and create an initial version of the global 
#	configuration object.
from . import configuration
config = configuration.load()

#	Create the root logger.
log = logger()
log.info(f'Initializing...')

#	Carefully import components of the `core.plugins` module to perserve the 
#	`canvas.plugins` psuedo-package through which loaded plugins are accessed.
from .core.plugins import load_all_plugins, get_path_occurrences

#	Update the configuration object with plugin configurations and wrap it for
#	better key error readback.
config = configuration.finalize(config)
log.debug(f'Runtime configuration: {pprint.pformat(config)}')

#	`canvas.core` only exports a subset of its contents.
from .core import *
from .launch import *

#	Import the model and controllers packages for initialization.
from . import model, controllers

#	Load all plugins. Has the side effect of populating the `canvas.plugins` 
#	namespace.
load_all_plugins()

#	Invoke pre-initialization callbacks. These are used to prepare for 
#	initialization, and can only assume the core to be importable.
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
