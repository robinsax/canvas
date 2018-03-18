#	coding utf-8
'''
Request parsing method definitions.
'''

from ..exceptions import UnsupportedMediaType
from ..namespace import export
from .json_io import deserialize_json

_parsers = dict()

@export
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
		return deserialize_json(body_data)
	except JSONDecodeError as ex:
		raise BadRequest('Invalid body syntax') from None