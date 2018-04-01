#	coding utf-8
'''
The canvas core contains fundamental system logic and namespaces which are
already in the root package.
'''

from werkzeug.serving import run_simple

from ..namespace import export
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

define_callback_type('pre_init', arguments=False)
define_callback_type('init', arguments=False)
define_callback_type('post_init', arguments=False)

_route_map = None

@export
def get_routing():
	return _route_map

@export
def get_controllers():
	controllers = []
	for route, controller in _route_map.items():
		if controller not in controllers:
			controllers.append(controller)
	return controllers

@export
def initialize():
	global _route_map
	if _route_map is not None:
		return

	invoke_callbacks('pre_init')

	load_config()
	load_plugins()

	invoke_callbacks('init')

	create_node_interface()
	create_render_environment()
	load_palette()

	_route_map = create_controllers()
	create_routing(_route_map)

	initialize_model()

	invoke_callbacks('post_init')

@export
def serve(port=80):
	initialize()

	run_simple('0.0.0.0', port, application)
