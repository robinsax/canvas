# coding: utf-8
'''
This package contains fundamental system logic including request handling entry 
and exit, archetectural archetypes, the model system, asset management, and
other features.
'''

from ..configuration import load_config
from ..utils import create_callback_registrar, logger
from .. import __version__
from .views import View, PageView, ErrorView, alter_root_page_view, view
from .controllers import Controller, Endpoint, Page, controller, endpoint, \
	page, create_controllers
from .plugins import plugin_base_path, load_plugins, get_path_occurrences, \
	get_path
from .request_context import RequestContext
from .request_errors import on_error, get_error_response
from .request_handler import on_request_received, handle_request
from .request_parsers import parse_datetime, request_body_parser, \
	parse_request_body, parse_json_request
from .responses import create_json, create_redirect, create_page
from .routing import RouteVariable, RouteString, create_routing, resolve_route, \
	on_routing, routing_diag
from .assets import Palette, Asset, directive, apply_directives, \
	transpile_jsx, compile_less, get_palette, get_asset, new_asset
from .model import ColumnType, BasicColumnType, TypeAdapter, Model, Table, \
	Column, CheckConstraint, PrimaryKeyConstraint, NotNullConstraint, \
	UniquenessConstraint, RegexConstraint, Session, Unique, RangeConstraint, \
	type_adapter, model, create_session, initialize_model, dictized_property, \
	dictize, update_column_types, relational_property

#	Create a logger.
log = logger(__name__)

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

	#	Initialize the model and create the global routing.
	initialize_model()
	create_routing(create_controllers())
	
	#	Invoke finalization callbacks.
	on_post_init.invoke()
	log.info('canvas %s initialized'%__version__)

def serve(port=80):
	'''Run the single-threaded debug server on `port`.'''
	from werkzeug.serving import run_simple

	initialize()
	run_simple('localhost', port, handle_request)
