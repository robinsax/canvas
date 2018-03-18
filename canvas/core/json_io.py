#	coding utf-8
'''
Implicit JSON serialization and deserialization.
'''

import json

from ..exceptions import Unrecognized
from ..namespace import export

_serializers = []
_deserializers = []

@export
def json_serializer(*types):
	def json_serializer_wrap(func):
		func.__serializes__ = types
		_serializers.append(types)
		return func
	return json_serializer_wrap

@export
def json_deserializer(func):
	_deserializers.append(func)
	return func

@export
def serialize_json(obj, fallback=None):
	def serialize_default(value):
		for serializer in _serializers:
			for typ in serializer.__serializes__:
				if isinstance(obj, typ):
					return serializer(obj)

		if fallback:
			return fallback(obj)

		raise TypeError(type(obj))
	
	return json.dumps(obj, default=serialize_default)

@export
def deserialize_json(data):
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

	return json.loads(data, object_hook=deserialize_hook)
