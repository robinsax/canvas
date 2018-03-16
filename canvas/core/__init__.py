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

define_callback_type('pre_init', arguments=False)
define_callback_type('init', arguments=False)
define_callback_type('post_init', arguments=False)

_initialized = False

@export
def initialize():
	global _initialized
	if _initialized:
		return
	_initialized = True

	invoke_callbacks('pre_init')

	load_config()
	load_plugins()

	invoke_callbacks('init')

	create_node_interface()
	create_render_environment()
	load_palette()

	route_map = create_controllers()
	create_routing(route_map)

	initialize_model()

	invoke_callbacks('post_init')

@export
def serve(port=80):
	initialize()

	run_simple('0.0.0.0', port, application)
