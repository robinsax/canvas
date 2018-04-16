#	coding utf-8
'''
Implicit JSON serialization and deserialization.
'''

import json

from datetime import datetime

from ..exceptions import Unrecognized
from ..namespace import export, export_ext
from .model.model import Model
from .model import dictize

_serializers = []
_deserializers = []

@export_ext
def json_serializer(*types):
	def json_serializer_wrap(func):
		func.__serializes__ = types
		_serializers.append(func)
		return func
	return json_serializer_wrap

@export_ext
def json_deserializer(func):
	_deserializers.append(func)
	return func

@export
def serialize_json(obj, fallback=None):
	def serialize_default(value):
		for serializer in _serializers:
			for typ in serializer.__serializes__:
				if isinstance(value, typ) or issubclass(type(value), typ):
					return serializer(value)

		if fallback:
			return fallback(value)

		raise TypeError(type(value))
	
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

@json_serializer(datetime)
def serialize_datetime(datetime_obj):
	from ..configuration import config

	return datetime_obj.strftime(config.datetime.output_format)

@json_serializer(Model)
def serialize_model(model):
	return serialize_json(dictize(model))
