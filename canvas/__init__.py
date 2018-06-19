# coding: utf-8
'''
canvas is a full-stack web application framework for building API-driven,
reactive web applications.
'''

#	Define the version.
__version__ = '0.3a'

import os
import sys
import inspect

#	Locate the current directory.
__home__ = os.path.abspath(
	os.path.dirname(
		os.path.dirname(inspect.getfile(sys.modules[__name__]))
	)
)
#	Define the supported verb set.
__verbs__ = ('get', 'post', 'put', 'patch', 'delete', 'options')

#	Check whether requirements have been installed.
__installed__ = True
try:
	import werkzeug, psycopg2, pyxl
except ImportError:
	__installed__ = False

#	Initialize.
from .exceptions import InvalidSchema, InvalidQuery, InvalidTag, InvalidAsset, \
	AssetError, Unrecognized, IllegalEndpointRoute, DependencyError, \
	HTTPException, BadRequest, Unauthorized, NotFound, UnsupportedVerb, \
	OversizeEntity, UnsupportedMediaType, UnprocessableEntity, \
	ValidationErrors, InternalServerError
from .utils import cached_property, logger
from .configuration import config, plugin_config
from .json_io import serialize_json, deserialize_json, serialize_datetime
from .cli import launcher, launch_cli

if __installed__:
	#	Initialize core.
	from .core import View, Column, CheckConstraint, PrimaryKeyConstraint, \
		NotNullConstraint, UniquenessConstraint, RegexConstraint, Unique, \
		alter_root_page_view, view, controller, endpoint, page, get_path, \
		on_error, on_request_received, parse_datetime, create_json, \
		create_redirect, create_page, on_routing, type_adapter, model, \
		create_session, resolve_route, dictized_property, dictize, \
		handle_request as application, initialize
	from . import ext, plugins
