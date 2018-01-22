#	coding utf-8
'''
Psycopg2 type adaption extensions.
'''

import json
import uuid

from psycopg2.extensions import (
	adapt, register_adapter,
	new_type, register_type
)

#	Relevant Postgres type OIDs.
JSON_OID = 114
UUID_OID = 2950

class JSONAdapter:
	'''
	An adapter for the JSON column type.
	'''

	def __init__(self, data):
		self.data = data

	def getquoted(self):
		'''
		Return a bytes representation of the escaped JSON
		content with a type prefix.
		'''
		if self.data is None:
			#	Store as NULL.
			return None
		
		return adapt(f'{json.dumps(self.data)}').getquoted() + b'::json'

class UUIDAdapter:
	'''
	An adapter for the UUID column type.
	'''

	def __init__(self, id):
		self.id = id

	def getquoted(self):
		'''
		Return bytes containing the hexidecimal 
		representation of this UUID.
		'''
		if self.id is None:
			#	Store as NULL.
			return None
		
		return adapt(self.id.hex).getquoted()

def cast_json(value, cur):
	'''
	A typecaster for the JSON column type.
	'''
	if value is None:
		#	NULL was read.
		return None

	return json.loads(value)

def cast_uuid(value, cur):
	'''
	A typecaster for the UUID column type.
	'''
	if value is None:
		#	NULL was read.
		return None

	return uuid.UUID(value)

#	Register adapters.
register_adapter(list, JSONAdapter)
register_adapter(dict, JSONAdapter)
register_adapter(uuid.UUID, UUIDAdapter)

#	Register typecasters.
JSON = new_type((JSON_OID,), 'JSON', cast_json)
UUID = new_type((UUID_OID,), 'UUID', cast_uuid)
register_type(JSON)
register_type(UUID)
