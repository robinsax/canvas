#	coding utf-8
'''
Type adaption via psycopg2.
'''

import uuid

from datetime import datetime

from psycopg2.extensions import (
	adapt, 
	register_adapter,
	new_type, 
	register_type
)

from ...namespace import export_ext
from ...utils import patch_type
from ..json_io import serialize_json, deserialize_json

JSON_OID = 114
UUID_OID = 2950

_adapted_types = [int, float, str, bytes, datetime]

@export_ext
def type_adapter(type_name, oid, *types):
	def type_adapter_wrap(cls):
		patched = patch_type(cls, TypeAdapter)
		instance = patched()

		class PsuedoAdapter:

			def __init__(self, data):
				self.data = data

			def getquoted(self):
				return instance.adapt(self.data)
			
		for typ in types:
			register_adapter(typ, PsuedoAdapter)
		_adapted_types.extend(types)

		def psuedo_cast(value, cursor):
			return instance.cast(value)
		register_type(new_type((oid,), type_name, psuedo_cast))

		return patched
	return type_adapter_wrap

class TypeAdapter:

	def existing_adaption(self, obj):
		return adapt(obj).getquoted()

	def adapt(self, obj):
		raise NotImplementedError()

	def cast(self, value):
		raise NotImplementedError()

@type_adapter('JSON', JSON_OID, list, dict)
class JSONAdapter:

	def adapt(self, obj):
		if obj is None:
			return None
		return self.existing_adaption(serialize_json(obj)) + b'::json'

	def cast(self, value):
		if value is None:
			return None
		return deserialize_json(value)

@type_adapter('UUID', UUID_OID, uuid.UUID)
class UUIDAdapter:
	
	def adapt(self, obj):
		if obj is None:
			return None
		return self.existing_adaption(obj.hex)

	def cast(self, value):
		if value is None:
			return None
		return uuid.UUID(value)
