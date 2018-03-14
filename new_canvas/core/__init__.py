#	coding utf-8
'''
The canvas core contains fundamental system logic and namespaces which are
already in the root package.
'''

#	TODO: shit packaging
_route_map = dict()

from werkzeug.serving import run_simple

from ..namespace import export
from ..callbacks import define_callback_type, invoke_callbacks
from ..controllers import create_controllers
from ..routing import update_routing
from .request_handler import handle_request

application = handle_request

define_callback_type('init', arguments=False)

@export
def initialize():
	invoke_callbacks('init')

	route_map = create_controllers(_route_map)
	update_routing(route_map)

@export
def serve(port=80):
	initialize()

	run_simple('0.0.0.0', port, application)
