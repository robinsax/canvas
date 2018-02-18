#	coding utf-8
'''
Column and column type definitions.
'''

import re
import json
import uuid
import datetime as dt

from types import LambdaType

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

#	TODO: Refactor these imports.
from . import (
	_PushResolveNow,
	_all_enum
)

class ColumnType:
	'''
	`ColumnType`s are attributes of `Column`s that store information about the
	SQL representation of the type.
	'''

	#	TODO: Extend `input_type` capabilities.
	def __init__(self, sql_type, input_type='text', default=_sentinel):
		'''
		Define a new column type.

		:sql_type The name of this type in PostgreSQL.
		:input_type The type of input to use for this column type if HTML 
			forms.
		:default The default value with which to populate attributes in this 
			column.
		'''
		self.sql_type, self.input_type = sql_type, input_type
		self.default = default

	def resolve(self, owner_column):
		'''
		Resolve this column type given the owner column.
		'''
		#	Update owner columns default if it wasn't specified.
		if owner_column.default is _sentinel:
			owner_column.default = self.default

class ForeignKeyColumnType(ColumnType):
	'''
	A foreign key column type with target column reference.
	'''

	def __init__(self, reference_str):
		'''
		Create a new foreign key column type referencing the table and column 
		specified in `reference_str`.
		'''
		super().__init__('FOREIGN KEY')
		self.reference_str = reference_str

	def resolve(self, owner_column):
		'''
		Mixin a `reference` attribute to `owner_column` referencing the target
		column.
		'''
		from . import _all_orm
		
		#	Invoke super.
		super().resolve(owner_column)
		
		#	Parse the reference string, locate the table and column.
		try:
			refd_table_name, refd_column_name = self.reference_str.split('.')
			refd_table = _all_orm[refd_table_name]
			refd_column = refd_table.__schema__[refd_column_name]
		except:
			raise ColumnDefinitionError(f'Malformed foreign key {self.reference_str}')
		
		#	Assert the target was already created.
		if not refd_table.__created__:
			raise _PushResolveNow(refd_table)
		
		#	Populate owner with the targeted column.
		owner_column.reference = refd_column

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
		#	The type of this column is the name of the enumerable type.
		super().__init__(enum_name)

		#	Retrieve and store a class reference.
		self.enum_cls = _all_enum[enum_name]

#	Basic column type definitions mapping regular expressions to type 
#	objects. When a column type string matches the key regex, the corresponding 
#	column type object is used for that column.
_column_types = {} 

@callback.pre_init
def define_column_types():
	'''
	Populate the column types list, then allow plugins to override or extend 
	it.
	'''
	#	Define the basic contents.
	_column_types.update({
		'int(?:eger)*': ColumnType('INTEGER', 'number'),
		'real|float': ColumnType('REAL'),
		'serial': ColumnType('SERIAL'),
		'blob': ColumnType('BYTEA', 'file'),
		'text': ColumnType('TEXT'),
		'longtext': ColumnType('TEXT', 'textarea'),
		'json': ColumnType('JSON'),
		'bool(?:ean)*':	ColumnType('BOOLEAN', 'checkbox'),
		'uuid': ColumnType('CHAR(32)', default=lambda: uuid.uuid4()),
		'pw|pass(?:word)*': ColumnType('TEXT', 'password'),
		#	TODO: Better date inputs.
		'^date$': ColumnType('DATE', 'date'),
		'^time$': ColumnType('TIME', 'time'),
		'dt|datetime': ColumnType('TIMESTAMP', 'datetime-local'),
		'fk:(.+)': lambda *args: ForeignKeyColumnType(*args),
		'enum:(.+)': lambda *args: EnumColumnType(*args),
	})
	#	Allow plugins to modify.
	call_registered('column_types_defined', _column_types)

class Column(SQLExpression):
	'''
	The class-level representation of a table column, placed as a class 
	attribute by the `model.schema()` decorator.

	Stores type information and generates an SQL-serializable expression 
	on comparison.
	'''
	
	def __init__(self, type_str, constraints=[], default=_sentinel, primary_key=False):
		'''
		Create a new column.

		:type_str A string representation of the column type.
		:default The default value to populate this column with. Default 
			values are populated after row insertion since they may be 
			resolved within Postgres.
		:primary_key Whether or not this column is the table's primary key.
		'''
		#	Store the type definition to be parsed by `resolve_type()`.
		self.type_str = type_str

		self.constraints = constraints
		self.default, self.primary_key = default, primary_key

		#	Store placeholder values.
		self.type, self.model, self.name = (None,)*3

	def resolve(self, model):
		'''
		Resolve this column, including its type and constraints.
		'''
		#	Store the parent model.
		self.model = model

		#	Resolve type
		for regex, typ in _column_types.items():
			match = re.match(regex, self.type_str, re.I)
			if match is not None:
				#	This column type was specified.
				if isinstance(typ, LambdaType):
					#	Invoke type generation.
					self.type = typ(*match.groups())
				else:
					#	Singleton type; assign.
					self.type = typ
				break
		
		#	Assert a column type was found.
		if self.type is None:
			raise ColumnDefinitionError(f'Unknown column type {self.type_str}')

		#	Allow the type to resolve.
		self.type.resolve(self)

		#	Allow constraints to resolve.
		for constraint in self.constraints:
			constraint.resolve(self)

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
	def count(self):
		'''
		Return the COUNT of this column when queried.
		'''
		return SQLAggregatorCall('COUNT', self)

	def is_max(self):
		'''
		Return a query condition that this column is maximal.
		'''
		return SQLAggregatorCall('MAX', self)

	def is_min(self):
		'''
		Return a query condition that this column is minimal.
		'''
		return SQLAggregatorCall('MIN', self)

	#	This one is sneaky...
	def __iter__(self):
		return iter([
			SQLAggregatorCall('MIN', self, weight=0),
			SQLAggregatorCall('MAX', self)
		])
