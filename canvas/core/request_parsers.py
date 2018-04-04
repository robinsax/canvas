#	coding utf-8
'''
Request parsing method definitions.
'''

from json import JSONDecodeError

from ..exceptions import (
	UnsupportedMediaType, 
	BadRequest
)
from ..namespace import export_ext
from .dictionaries import RequestParameters
from .json_io import deserialize_json

_parsers = dict()

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
		raise BadRequest('Invalid body syntax') from None

	return RequestParameters(obj) if isinstance(obj, dict) else obj