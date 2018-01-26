#	coding utf-8
'''
Type adaption via psycopg2.
'''

import json
import uuid
import datetime as dt

from psycopg2.extensions import (
	adapt, 
	register_adapter,
	new_type, 
	register_type
)

__all__ = [
	'adapter',
	'TypeAdapter'
]

#	Declare relevant Postgres type OIDs.
JSON_OID = 114
UUID_OID = 2950

#	A list of types known to be adaptable.
#	TODO: Support date and time individually too.
_adapted_types = [int, float, str, dt.datetime]

def adapter(cls):
	'''
	A decorator for `TypeAdapter` actualization.
	'''
	inst = cls()
	#	Add to the list of adaptable types.
	_adapted_types.extend(inst.types)

	#	Create and register adapter.
	class PsuedoAdapter:

		def __init__(self, data):
			self.data = data

		def getquoted(self):
			return inst.adapt(self.data)
		
	for typ in inst.types:
		register_adapter(typ, PsuedoAdapter)

	#	Register and register caster.
	def psuedo_cast(value, cursor):
		return inst.cast(value)
	register_type(new_type((inst.oid,), inst.type_name, psuedo_cast))

	return cls

class TypeAdapter:
	'''
	The base type adaption class.

	A psycopg2 type adapter with a casting classmethod.
	'''

	def __init__(self, type_name, oid, *types):
		'''
		Declare the types adapted by the inheriting `TypeAdapter`.
		'''
		self.type_name, self.oid = type_name, oid
		self.types = types
		
	def existing_adaption(self, obj):
		'''
		Helper method. Return `obj` adapted and quoted by an existing means.
		'''
		return adapt(obj).getquoted()

	def adapt(self, obj):
		'''
		Return `obj` adapted to bytes.
		'''
		raise NotImplemented()

	def cast(self, value):
		'''
		Return `value` cast to one of the adapted types.
		'''
		raise NotImplemented()

@adapter
class JSONAdapter(TypeAdapter):
	'''
	An adapter for the JSON column type.
	'''

	def __init__(self):
		super().__init__('JSON', JSON_OID, list, dict)

	def adapt(self, obj):
		if obj is None:
			#	Adapt to NULL.
			return None
		return self.existing_adaption(json.dumps(obj)) + b'::json'

	def cast(self, value):
		if value is None:
			#	NULL was read.
			return None
		return json.loads(value)

@adapter
class UUIDAdapter(TypeAdapter):
	'''
	An adapter for the UUID column type.
	'''

	def __init__(self):
		super().__init__('UUID', UUID_OID, uuid.UUID)
	
	def adapt(self, obj):
		if obj is None:
			#	Adapt to NULL.
			return None
		return self.existing_adaption(obj.hex)

	#	TODO: Not using.
	def cast(self, value):
		if value is None:
			#	NULL was read.
			return None
		return uuid.UUID(value)
