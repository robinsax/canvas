#	coding utf-8
'''
Psycogpg2 type casting configuration
'''

#	TODO: Package these beside columns?
#	TODO: XML support should be a plugin

import json
import uuid
import lxml.etree as et

from psycopg2.extensions import (
	adapt, register_adapter,
	new_type, register_type
)

#	Declare OIDs for supported Postgres version
JSON_OID = 114
XML_OID = 142
UUID_OID = 2950

class JSONAdapter:
	'''
	An adapter for the JSON column type
	'''

	def __init__(self, data):
		self.data = data

	def getquoted(self):
		if self.data is None:
			return None
		return adapt(f'{json.dumps(self.data)}::json')

class XMLAdapter:
	'''
	An adapter for the XML column type
	'''

	def __init__(self, elem):
		self.elem = elem

	def getquoted(self):
		if self.elem is None:
			return None
		return adapt(f'{et.tostring(self.elem)}::xml')

class UUIDAdapter:
	'''
	An adapter for the UUID column type
	'''

	def __init__(self, id):
		self.id = id

	def getquoted(self):
		if self.id is None:
			return None
		#	Adapt to Postgres format
		return adapt(self.id.hex).getquoted()

def cast_json(value, cur):
	'''
	A typecaster for the JSON column type
	'''
	if value is None:
		return None
	return json.loads(value)

def cast_xml(value, cur):
	'''
	A typecaster for the XML column type
	'''
	if value is None:
		return None
	return et.fromstring(value)

def cast_uuid(value, cur):
	'''
	A typecaster for the UUID column type
	'''
	if value is None:
		return None
	return uuid.UUID(value)

#	Register adapters
register_adapter(list, JSONAdapter)
register_adapter(dict, JSONAdapter)
register_adapter(type(et.Element('div')), XMLAdapter)
register_adapter(uuid.UUID, UUIDAdapter)
#	Register typecasters
JSON = new_type((JSON_OID,), 'JSON', cast_json)
XML = new_type((XML_OID,), 'XML', cast_xml)
UUID = new_type((UUID_OID,), 'UUID', cast_uuid)
register_type(JSON)
register_type(XML)
register_type(UUID)