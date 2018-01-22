#	coding utf-8
'''
Column class and column type declarations.
'''

import re
import json
import uuid
import datetime as dt

from ..exceptions import (
	ColumnDefinitionError, 
	MappedTypeError
)
from ..utils import call_registered
from . import _all_enum

#	An object used to identify un-initialized
#	columns when issuing row creation.
_sentinel = object()

class ColumnType:
	'''
	A column type definition class enforcing and SQL type name,
	form input type, and default value.

	Column types are transparent to plugins in the majority of
	use cases, but can be assumed stable.
	'''

	def __init__(self, sql_type, input_type='text', default=_sentinel):
		'''
		Define a new column type.
		
		TODO: Extend `input_type` capabilities.

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

class EnumColumnType(ColumnType):
	'''
	An enumerable type column type.

	TODO: Form inputs for this type.
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
_column_types = {
	'int(?:eger)*': ColumnType('INTEGER', 'number'),
	'real|float': ColumnType('REAL'),
	'serial': ColumnType('SERIAL'),
	'(?:long)*text': ColumnType('TEXT'),
	'json': ColumnType('JSON'),
	'bool(?:ean)*':	ColumnType('BOOLEAN', 'checkbox'),
	'uuid': ColumnType('CHAR(32)', default=lambda: uuid.uuid4()),
	'pw|pass(?:word)*': ColumnType('TEXT', 'password'),
	'dt|datetime': ColumnType('TIMESTAMP')
}

#	Allow plugins to extend the basic column type definitions.
call_registered('column_types_defined', _column_types)

class _ColumnComparator:
	'''
	A value comparison used to allow class-attribute-based
	SQL queries.

	The nature of this object, aside from the existance of a
	`group()` method, is not exposed outside of this package.
	'''

	def __init__(self, left, right, operator):
		'''
		Create a column comparator representing a comparsion
		of `left` to `right` using the SQL operator `operator`.
		'''
		#	Left and right sides of the expression.
		self.left, self.right = (left, right)
		#	The operator as a string.
		self.operator = operator
		
		#	Placeholder properties modifiable by later
		#	unary operations.
		self.inverted = False
		self.grouped = False

	def group(self):
		'''
		*Group* this comparison expression to give it 
		precedence.
		'''
		self.grouped = True
		return self
	
	def __invert__(self):
		'''
		Group and logically invert this comparison 
		expression.
		'''
		self.grouped = True
		self.inverted = True
		return self

	def __and__(self, other):
		'''
		Return a conjunction of this expression and another.
		'''
		return _ColumnComparator(self, other, 'AND')

	def __or__(self, other):
		'''
		Return a disjunction of this expression and another.
		'''
		return _ColumnComparator(self, other, 'OR')

	def __repr__(self):
		'''
		Return a debugging representation. 
		'''
		return (
			f'<{self.__class__.__name__}: left={self.left},' 
			+ f'opr={self.opr}, right={self.right}>'
		)

class Column:
	'''
	The class-level representation of a table column, placed as
	a class attribute by the `model.schema()` decorator.

	Stores type information and generates SQL-serializable 
	expression on comparison.
	'''
	
	def __init__(self, type_str, constraints=[], default=None, 
			primary_key=False):
		'''
		Create a new column.

		:type_str A string representation of the column type.
		:default The default value to populate this column with. 
			Default values are populated after row insertion since 
			they may be resolved within Postgres.
		:primary_key Whether or not this column is the table's
			primary key.
		'''
		#	Resolve the type string to a type object.
		self.type = None
		if type_str.startswith('fk:'):
			self.type = ForeignKeyColumnType(type_str[3:])
		elif type_str.startswith('enum:'):
			self.type = EnumColumnType(type_str[5:])
		else:
			#	Check against each regular expression key.
			for regex, typ in _column_types.items():
				match = re.match(regex, type_str, re.I)
				if match is not None:
					#	Matched; use this column type.
					self.type = typ
					break
		
		#	Assert a column type was found.
		if self.type is None:
			raise ColumnDefinitionError(f'Unknown column type {type_str}')
		
		#	Popluate constraint attribute and store the list.
		if not isinstance(constraints, (list, tuple)):
			#	The `constraints` parameter was passed a single
			#	object.
			constraints = (constraints,)
		for constraint in constraints:
			constraint.target_column = self
		self.constraints = constraints

		#	Find and store the highest-precedence default value.
		#	Guarenteed to be at least the `_sentinel` object.
		self.default = default if default is not None else self.type.default

		#	Store primary key flag.
		self.primary_key = primary_key

		#	Save placeholder values for a model class reference
		#	and column name.
		self.model = None
		self.name = None
		
	def get_default(self):
		'''
		Return the default value for this column, resolving
		it if it's callable.
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

	#	Comparisons yield `_ColumnComparator`s
	def __eq__(self, other):
		return _ColumnComparator(self, other, '=')

	def __ne__(self, other):
		return _ColumnComparator(self, other, '<>')

	def __lt__(self, other):
		return _ColumnComparator(self, other, '<')

	def __le__(self, other):
		return _ColumnComparator(self, other, '<=')

	def __gt__(self, other):
		return _ColumnComparator(self, other, '>')

	def __ge__(self, other):
		return _ColumnComparator(self, other, '>=')

	def __repr__(self):
		'''
		Return a debugging representation. 
		'''
		return ( 
			f'<{self.__class__.__name__}: type={repr(self.type)},'
			+ f' table={self.model.__table__}>'
		)
