# coding: utf-8
'''
Python to Postgres type adaption is extended via the `type_adapter` decorator.
'''

import uuid

from datetime import datetime
from psycopg2.extensions import adapt, register_adapter, new_type, \
		register_type

from ...json_io import serialize_json, deserialize_json

#	Declare the list of adapted known types.
_adapted_types = [int, float, str, bytes, datetime]

#	Declare the OIDs of base custom adaptions.
JSON_OID = 114
UUID_OID = 2950

class TypeAdapter:
	'''
	The base type adapter class, implicitly extended with the `type_adapter` decorator.
	'''

	def existing_adaption(self, obj):
		'''Return the adaption of `obj` by an existing method.'''
		return adapt(obj).getquoted()

	def adapt(self, obj):
		'''Adapt a Python object to it's Postgres representation.'''
		raise NotImplementedError()

	def cast(self, value):
		'''Cast a Postgres representation to a Python object.'''
		raise NotImplementedError()

def type_adapter(type_name, oid, *types):
	'''
	A decorator for type adapter class registration. Implicitly causes 
	extension from `TypeAdapter`.

	::type_name The name of the Postgres type.
	::oid The OID of the Postgres type.
	::types The Python types adapted by this type adapter.
	'''
	def type_adapter_wrap(cls):
		#	Patch the type to extend TypeAdapter.
		patched = type(cls.__name__, (cls, TypeAdapter), dict())
		#	Create the singleton instance.
		instance = patched()
		
		#	Create and register the adapter.
		class PsuedoAdapter:

			def __init__(self, data):
				self.data = data

			def getquoted(self):
				return instance.adapt(self.data)
		
		for typ in types:
			register_adapter(typ, PsuedoAdapter)
		_adapted_types.extend(types)

		#	Create and register a pseudo-caster.
		def psuedo_cast(value, cursor):
			return instance.cast(value)
		register_type(new_type((oid,), type_name, psuedo_cast))

		return patched
	return type_adapter_wrap

@type_adapter('JSON', JSON_OID, list, dict)
class JSONAdapter:
	'''A JSON list or object type adapter.'''

	def adapt(self, obj):
		if obj is None:
			return None
		return b''.join((self.existing_adaption(serialize_json(obj)), b'::json'))

	def cast(self, value):
		if value is None:
			return None
		return deserialize_json(value)

@type_adapter('UUID', UUID_OID, uuid.UUID)
class UUIDAdapter:
	'''
	A UUID adapter. The caster is ignored by canvas's default UUID storage 
	mechanism.
	'''
	
	def adapt(self, obj):
		if obj is None:
			return None
		return self.existing_adaption(obj.hex)

	def cast(self, value):
		if value is None:
			return None
		return uuid.UUID(value)
