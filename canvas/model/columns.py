#	coding utf-8
'''
Column class and column type declarations.
'''

import re
import json
import uuid
import datetime as dt

from ..exceptions import ColumnDefinitionError
from ..utils import callback, call_registered

#	An object used to identify un-initialized columns when issuing row 
#	creation.
_sentinel = object()

from .sql_factory import (
	SQLExpression,
	SQLComparison,
	SQLAggregatorCall
)

#	TODO: Refactor this import.
from . import _all_enum

class ColumnType:
	'''
	A column type definition class enforcing and SQL type name,
	form input type, and default value.

	Column types are transparent to plugins in the majority of
	use cases, but can be assumed stable.
	'''

	#	TODO: Extend `input_type` capabilities.
	def __init__(self, sql_type, input_type='text', default=_sentinel):
		'''
		Define a new column type.

		:sql_type The name of this type in PostgreSQL.
		:input_type The type of input to use for this column type
			if HTML forms.
		:default The default value with which to populate
			attributes in this column.
		'''
		self.sql_type, self.input_type = sql_type, input_type
		self.default = default

	def __repr__(self):
		return f'<{self.__class__.__name__}: sql_type={self.sql_type}>'

class ForeignKeyColumnType(ColumnType):
	'''
	A foreign key column type with target column reference.
	'''

	def __init__(self, target_name):
		'''
		Create a new foreign key column type referencing the
		table and column specified in `target_name`.
		'''
		super().__init__('FOREIGN KEY')
		self.target_name = target_name
		self.target_model = None

#	TODO: Form inputs for this type.
class EnumColumnType(ColumnType):
	'''
	An enumerable type column type.
	'''

	def __init__(self, enum_name):
		'''
		Create a enum column type targeting the enum 
		registered as `enum_name`.

		:enum_name The name of an enumerable type
			decorated with `@model.enum`.
		'''
		#	The type of this column is the name of the 
		#	enumerable type.
		super().__init__(enum_name)

		#	Retrieve and store a class reference.
		self.enum_cls = _all_enum[enum_name]

#	Basic column type definitions mapping regular expressions
#	to type objects. When a column type string matches the
#	key regex, the corresponding column type object is used
#	for that column.
_column_types = {} 

@callback.pre_init
def define_column_types():
	_column_types.update({
		'int(?:eger)*': ColumnType('INTEGER', 'number'),
		'real|float': ColumnType('REAL'),
		'serial': ColumnType('SERIAL'),
		'(?:long)*text': ColumnType('TEXT'),
		'json': ColumnType('JSON'),
		'bool(?:ean)*':	ColumnType('BOOLEAN', 'checkbox'),
		'uuid': ColumnType('CHAR(32)', default=lambda: uuid.uuid4()),
		'pw|pass(?:word)*': ColumnType('TEXT', 'password'),
		'dt|datetime': ColumnType('TIMESTAMP')
	})
	#	Allow plugins to extend the basic column type definitions.
	call_registered('column_types_defined', _column_types)

class Column(SQLExpression):
	'''
	The class-level representation of a table column, placed as a class 
	attribute by the `model.schema()` decorator.

	Stores type information and generates an SQL-serializable expression 
	on comparison.
	'''
	
	def __init__(self, type_str, constraints=[], default=None, 
			primary_key=False):
		'''
		Create a new column.

		:type_str A string representation of the column type.
		:default The default value to populate this column with. Default 
			values are populated after row insertion since they may be 
			resolved within Postgres.
		:primary_key Whether or not this column is the table's primary key.
		'''
		#	Store attributes used by `compute_type()`.
		self.type_str = type_str
		self.default = default

		#	Populate constraint attribute and store the list.
		if not isinstance(constraints, (list, tuple)):
			#	The `constraints` parameter was passed a single object.
			constraints = (constraints,)
		self.constraints = constraints

		#	Store primary key flag.
		self.primary_key = primary_key

		#	Save placeholder values.
		self.type = None
		self.model = None
		self.name = None

	def compute_type(self):
		'''
		Parse the type definition of this column and initialize it 
		appropriatly.
		'''
		#	Resolve the type string to a type object.
		if self.type_str.startswith('fk:'):
			self.type = ForeignKeyColumnType(self.type_str[3:])
		elif self.type_str.startswith('enum:'):
			self.type = EnumColumnType(self.type_str[5:])
		else:
			#	Check against each regular expression key.
			for regex, typ in _column_types.items():
				match = re.match(regex, self.type_str, re.I)
				if match is not None:
					#	Matched; use this column type.
					self.type = typ
					break
		
		#	Assert a column type was found.
		if self.type is None:
			raise ColumnDefinitionError(f'Unknown column type {self.type_str}')

		#	Find and store the highest-precedence default value.
		#	Guarenteed to be at least the `_sentinel` object.
		if self.default is None:
			self.default = self.type.default

	def serialize(self, values):
		'''
		Return an SQL-serialized reference to this column.
		'''
		return f'{self.model.__table__}.{self.name}'
		
	def get_default(self):
		'''
		Return the default value for this column, resolving it if it's 
		callable.
		'''
		if callable(self.default):
			#	This is a callable that generates the default
			#	values.
			return self.default()

		#	This is a constant default.
		return self.default

	def value_for(self, model_obj):
		'''
		Return the value of this column for the given 
		model object.
		'''
		return getattr(model_obj, self.name)

	def set_value_for(self, model_obj, value):
		'''
		Set the value of this column on the given model 
		object.
		'''
		setattr(model_obj, self.name, value)

	def is_max(self):
		return SQLAggregatorCall('MAX', self)

	def is_min(self):
		return SQLAggregatorCall('MIN', self)

	#	Comparisons yield `SQLComparison`s
	def __eq__(self, other):
		return SQLComparison(self, other, '=')

	def __ne__(self, other):
		return SQLComparison(self, other, '<>')

	def __lt__(self, other):
		return SQLComparison(self, other, '<')

	def __le__(self, other):
		return SQLComparison(self, other, '<=')

	def __gt__(self, other):
		return SQLComparison(self, other, '>')

	def __ge__(self, other):
		return SQLComparison(self, other, '>=')

	#	Some builtin function calls yeild `SQLAggregatorCall`s.
	def __len__(self):
		return SQLAggregatorCall('COUNT', self)

	#	This one is sneaky...
	def __iter__(self):
		return iter([
			SQLAggregatorCall('MIN', self, weight=0),
			SQLAggregatorCall('MAX', self)
		])
