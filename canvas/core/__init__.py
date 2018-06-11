# coding: utf-8
'''
This package contains fundamental system logic including request handling entry 
and exit, archetectural archetypes, the model system, asset management, and
other features.
'''

from ..configuration import load_config
from ..utils import create_callback_registrar
from .controllers import create_controllers
from .plugins import load_plugins
from .routing import create_routing
from .request_handler import handle_request
from .templates import create_render_environment
from .styles import load_palette
from .node_interface import create_node_interface
from .model import initialize_model
from . import responses

#	Define the 2-stage initialization callback series.
on_init = create_callback_registrar()
on_post_init = create_callback_registrar()

#	A flag for function-locking initialize().
_initialized = False

def initialize():
	'''
	Initialize canvas by loading configuration, then plugins, then the asset, 
	model, and controller systems. Invokes the `on_pre_init`, `on_init`, and
	`on_post_init` callbacks.
	'''
	#	Lock re-initialization.
	global _initialized
	if _initialized:
		return
	_initialized = True

	#	Load plugins and configuration.
	load_config()
	load_plugins()
	
	#	Invoke initialization callbacks.
	on_init.invoke()

	#	Initialize the asset, model, and controller systems.
	initialize_assets()
	initialize_model()
	create_routing(create_controllers())

	#	Invoke finalization callbacks.
	on_post_init.invoke()

def serve(port=80):
	'''Run the single-threaded debug server on `port`.'''
	from werkzeug.serving import run_simple

	initialize()
	run_simple('0.0.0.0', port, handle_request)
