#	coding utf-8
'''
An extension of the Python JSON serialization and deserialization API with
improved extensibility and security.
'''

import json

from datetime import datetime

from .exceptions import Unrecognized

#	Define lists of type serializers and deserializers.
_serializers, _deserializers = list(), list()

def json_serializer(*types):
	'''
	The JSON serializer registration decorator.
	::types The types which to which this serializer applies.
	'''
	def json_serializer_wrap(func):
		func.__serializes__ = types
		_serializers.append(func)
		return func
	return json_serializer_wrap

def json_deserializer(func):
	'''The JSON deserializer registration decorator.'''
	_deserializers.append(func)
	return func

def serialize_json(obj, fallback=None, pretty=False):
	'''
	Serialize the JSONable object `obj` into a JSON string.
	::obj The JSONable object to serialize.
	::fallback A fallback serialization method.
	::pretty Whether to prettify the output.
	'''
	#	Define the aggregated fallback function.
	def serialize_default(value):
		#	Check serializers.
		for serializer in _serializers:
			for typ in serializer.__serializes__:
				if isinstance(value, typ) or issubclass(type(value), typ):
					return serializer(value)

		#	Check fallback.
		if fallback:
			return fallback(value)

		raise TypeError(type(value))
	
	return json.dumps(obj, default=serialize_default, 
			indent=4 if pretty else None)

def deserialize_json(json_str):
	'''Deserialize `json_str` into native data structures.'''
	#	Define the object deserializer hook.
	def deserialize_hook(dct):
		for key, value in dct.items():
			for deserializer in _deserializers:
				try:
					new_value = deserializer(value)
				except Unrecognized:
					continue
				
				dct[key] = new_value
				break
		return dct

	return json.loads(json_str, object_hook=deserialize_hook)

@json_serializer(datetime)
def serialize_datetime(datetime_obj):
	'''A datetime serializer that honours the configured output format.'''
	from ..configuration import config

	return datetime_obj.strftime(config.datetime.output_format)
