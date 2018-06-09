#	coding utf-8
'''
This module is used to collect the root namespace.
'''

from . import __installed__

from .exceptions import InvalidSchema, InvalidQuery, InvalidTag, InvalidAsset,
	AssetError, Unrecognized, IllegalEndpointRoute, DependencyError,
	HTTPException, BadRequest, Unauthorized, NotFound, UnsupportedVerb,
	OversizeEntity, UnsupportedMediaType, UnprocessableEntity, 
	ValidationErrors, InternalServerError
from .utils import create_callback_registrar, cached_property, \
	format_exception, logger
from .configuration import config, plugin_config
from .json_io import serialize_datetime, deserialize_json, serialize_datetime
