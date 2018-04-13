#	coding utf-8
'''
Request parsing method definitions.
'''

from base64 import b64decode
from datetime import datetime
from json import JSONDecodeError
from mimetypes import guess_extension

from ..exceptions import (
	UnsupportedMediaType, 
	BadRequest
)
from ..namespace import export, export_ext
from ..configuration import config
from .dictionaries import LazyAttributedDict, RequestParameters
from .json_io import deserialize_json

_parsers = dict()

@export
def parse_datetime(datetime_str):
	if not isinstance(config.datetime.input_format, (list, tuple)):
		config.datetime.input_format = (config.datetime.input_format,)

	for fmt in config.datetime.input_format:
		try:
			return datetime.strptime(datetime_str, fmt)
		except: pass
	
	raise BadRequest('Invalid datetime %s'%datetime_str) from None

@export_ext
def request_parser(*mimetypes):
	def request_parser_wrap(func):
		for mimetype in mimetypes:
			_parsers[mimetype] = func
		return func
	return request_parser_wrap

def parse_request(body, mimetype):
	if mimetype not in _parsers:
		raise UnsupportedMediaType(mimetype)
	
	return _parsers[mimetype](body)

@request_parser('application/json')
def parse_json_request(body):
	try:
		obj = deserialize_json(body)
	except JSONDecodeError as ex:
		raise BadRequest('Invalid request syntax') from None
	
	return RequestParameters(obj) if isinstance(obj, dict) else obj 
