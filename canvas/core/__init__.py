#	coding utf-8
'''
The canvas core contains fundamental system logic and namespaces which are
already in the root package.
'''

from werkzeug.serving import run_simple

from ..namespace import export, export_ext
from ..callbacks import define_callback_type, invoke_callbacks
from ..controllers import create_controllers
from ..configuration import load_config
from .plugins import load_plugins
from .routing import create_routing
from .request_handler import handle_request
from .templates import create_render_environment
from .styles import load_palette
from .node_interface import create_node_interface
from .model import initialize_model
from . import responses

application = handle_request
export('application')(application)

define_callback_type('pre_init')
define_callback_type('init')
define_callback_type('post_init')

_route_map = None

@export_ext
def get_routing():
	return _route_map

@export_ext
def get_controller(route):
	return _route_map.get(route, None)

@export_ext
def get_controllers():
	controllers = []
	for route, controller in _route_map.items():
		if controller not in controllers:
			controllers.append(controller)
	return controllers

def initialize_controllers():
	global _route_map
	
	_route_map = create_controllers()
	create_routing(_route_map)

@export
def initialize():
	if _route_map is not None:
		return

	invoke_callbacks('pre_init')

	load_config()
	load_plugins()
	
	invoke_callbacks('init')

	create_node_interface()
	create_render_environment()
	load_palette()

	initialize_model()
	initialize_controllers()

	invoke_callbacks('post_init')

@export
def serve(port=80):
	initialize()

	run_simple('0.0.0.0', port, application)
