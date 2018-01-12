#	coding utf-8
'''
Column types and instances
'''

import re
import json
import uuid

from ..exceptions import ColumnDefinitionError

#	Used to identify columns that have not
#	yet been initialized when issuing row 
#	creation
_sentinel = object()

#	The identity transform, used for most
#	column value serializations and
#	deserializations
_ident = lambda v: v

class ColumnType:
	'''
	Template for the majority of column types.
	'''

	def __init__(self, sql_type, input_type='text',
			default=_sentinel, serialize=_ident, 
			deserialize=_ident):
		'''
		Create a new column type
		:sql_type The name of this type in PostgreSQL
		:default The default value with which to populate
			attributes in this column
		:serialize A Python value to SQL serialization
			transform
		:deserialize A SQL serialization to Python value
			transform
		'''
		self.sql_type = sql_type
		self.input_type = input_type
		self.default = default
		self.serialize = serialize
		self.deserialize = deserialize

	def __repr__(self):
		return f'<{self.__class__.__name__}: sql_type={self.sql_type}>'

class ForeignKeyColumnType(ColumnType):
	'''
	Template for the foreign key column type, since
	it serializes differently.
	'''

	def __init__(self, target):
		'''
		Create a new foreign key column type
		pointing at `target`
		'''
		super().__init__('FOREIGN KEY')
		self.target = target
		self.target_model = None

class EnumColumnType(ColumnType):
	'''
	An enum column type, stored in database by 
	value name
	'''

	def __init__(self, enum_name):
		'''
		Create a enum column type targeting the enum 
		registered as `enum_name`
		'''
		super().__init__(enum_name)
		enum_cls = get_registered_by_name()[enum_name]
		self.serialize = lambda v: v.name
		self.deserialize = lambda v: enum_cls[v]

#	Define the basic column types
_column_types = {
	'int(?:eger)*': ColumnType('INTEGER', 'number'),
	'real|float': ColumnType('REAL'),
	'serial': ColumnType('SERIAL'),
	'(?:long)*text': ColumnType('TEXT'),
	'json': ColumnType('TEXT', serialize=json.dumps, deserialize=json.loads),
	'bool(?:ean)*':	ColumnType('BOOLEAN', 'checkbox'),
	'uuid': ColumnType('CHAR(32)', default=lambda: uuid.uuid4().hex),
	'pw|pass(?:word)*': ColumnType('TEXT', 'password')
}

class Column:
	'''
	The class-level ORM representation of a table column,
	decorated onto model classes. Holds a `ColumnType` and
	other column parameters. Generates a `ColumnComparator` when
	compared to allow `session.query()` syntax.
	'''

	def __init__(self, type_str, constraints=[], default=None, 
			primary_key=False):
		'''
		Create a new column.
		:type_str A string representation of the desired type
		:nullable Whether this column can contain `NULL`
		:default The default value to populate this column with. 
			Default values are set at insert-time, since they are 
			propogated to the database level
		:primary_key Whether or not this column is the table 
			primary key
		'''
		#	Get type
		self.type = None
		if type_str.startswith('fk:'):
			self.type = ForeignKeyColumnType(type_str[3:])
		elif type_str.startswith('enum:')
			self.type = EnumColumnType(type_str[5:])
		else:
			#	Check against each regular expression key
			for regex, type in _column_types.items():
				match = re.match(regex, type_str, re.I)
				if match is not None:
					#	Use this column type
					self.type = type
					break
		
		if self.type is None:
			#	Didn't match any types
			raise ColumnDefinitionError(f'Unknown column type {type_str}')
		
		#	Parse constraints and target them here
		if not isinstance(constraints, (list, tuple)):
			constraints = (constraints,)
		for constraint in constraints:
			constraint.target_column = self
		self.constraints = constraints

		#	Save default. If it wasn't specified by
		#	caller, fallback to the type default, which
		#	is at least _sentinel
		self.default = default if default is not None else type.default

		#	Save primary key flag
		self.primary_key = primary_key

		#	Save placeholders to be set on schema
		#	resolve
		self.model = None
		self.name = None
		
	def get_default(self):
		'''
		Return the default value for this column, resolving
		it if it's callable
		'''
		if callable(self.default):
			#	This is a generator (for example `UUID` 
			#	type), invoke it
			return self.default()
		#	Scalar constant default
		return self.default

	def value_for(self, model_obj):
		'''
		Return the value of this column on the
		given model object
		'''
		return getattr(model_obj, self.name)

	def set_value_for(self, model_obj, value):
		'''
		Set the value of this column on the
		given model object
		'''
		setattr(model_obj, self.name, value)

	def serialized_for(self, model_obj):
		'''
		Return the serialized value of this column
		on the given model object
		'''
		pre = self.value_for(model_obj)
		if pre is None:
			return None
		if pre is _sentinel:
			return _sentinel
		return self.type.serialize(pre)

	def deserialize_onto(self, model_obj, value):
		'''
		Deserialize the given value of this column
		onto the given model object
		'''
		if value is None:
			return None
		self.set_value_for(model_obj, self.type.deserialize(value))

	#	Comparison yields a `ColumnComparator`
	def __eq__(self, other):
		return ColumnComparator(self, other, '=')

	def __ne__(self, other):
		return ColumnComparator(self, other, '<>')

	def __lt__(self, other):
		return ColumnComparator(self, other, '<')

	def __lt__(self, other):
		return ColumnComparator(self, other, '<=')

	def __gt__(self, other):
		return ColumnComparator(self, other, '>')

	def __ge__(self, other):
		return ColumnComparator(self, other, '>=')

	def __repr__(self):
		return ( 
			f'<{self.__class__.__name__}: type={repr(self.type)},'
			+ f' table={self.model.__table__}>'
		)

class ColumnComparator:
	'''
	Yeilded by comparisions on model class column 
	attributes. Track the expression tree to be
	resolved to SQL be returning itself of a parent
	'''

	def __init__(self, left, right, operator):
		'''
		Create a new column comparator
		'''
		#	Left and right sides of the expression
		self.left, self.right = (left, right)
		#	The operator as a string
		self.operator = operator
		
		#	These properties are set later
		self.inverted = False
		self.grouped = False

	#	Unary operations yield self
	def group(self):
		self.grouped = True
		return self
	
	def __invert__(self):
		self.grouped = True
		self.inverted = True
		return self

	#	Comparisons yield parent objects
	def __and__(self, other):
		return ColumnComparator(self, other, 'AND')

	def __or__(self, other):
		return ColumnComparator(self, other, 'OR')

	def __repr__(self):
		return (
			f'<{self.__class__.__name__}: left={self.left},' 
			+ f'opr={self.opr}, right={self.right}>'
		)
