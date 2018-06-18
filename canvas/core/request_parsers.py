# coding: utf-8
'''
This module contains the request body parsing API as well as a client-
distrustful datetime parser.
'''

from base64 import b64decode
from datetime import datetime
from json import JSONDecodeError
from mimetypes import guess_extension

from ..exceptions import UnsupportedMediaType, BadRequest
from ..configuration import config
from ..dictionaries import AttributedDict, RequestParameters
from ..json_io import deserialize_json

#	Define the global mimetype to request body parser function map.
_parsers = dict()

def parse_datetime(datetime_str):
	'''
	Parse a client-supplied datetime as the configured format or raise a
	`BadRequest`.
	'''
	#	Multiple datetime formats are allowed in configuration, ensure the set
	#	is iterable.
	if not isinstance(config.datetime.input_format, (list, tuple)):
		config.datetime.input_format = (config.datetime.input_format,)
	
	#	Check each configured format, returning on success.
	for check_format in config.datetime.input_format:
		try:
			return datetime.strptime(datetime_str, check_format)
		except: pass
	
	#	No matching format was found.
	raise BadRequest('Invalid datetime %s'%datetime_str)

def request_body_parser(*mimetypes):
	'''
	The request body parser function registerar.
	::mimetypes The mimetypes which this parser can handle.
	'''
	def inner_request_body_parser(func):
		for mimetype in mimetypes:
			_parsers[mimetype] = func
		return func
	return inner_request_body_parser

@request_body_parser('application/json', 'text/json')
def parse_json_request(body_data):
	'''
	Parse an incoming JSON body, storing JSON objects as `RequestParameters`.
	'''
	#	Attempt deserialization.
	try:
		parsed = deserialize_json(body_data)
	except JSONDecodeError as ex:
		raise BadRequest('Invalid syntax in request JSON') from None
	
	#	Maybe wrap the root object.
	root_object = (
		RequestParameters(parsed) if isinstance(parsed, dict) else parsed
	)
	#	Propagate RequestParameters.
	RequestParameters.propagate_onto(root_object)
	return root_object

#	TODO: Handle charset.
def parse_request_body(body_data, mimetype, charset):
	'''Parse `body_data` as `mimetype` or raise `UnsupportedMediaType`.'''
	if mimetype not in _parsers:
		raise UnsupportedMediaType(mimetype)
	
	return _parsers[mimetype](body_data)
