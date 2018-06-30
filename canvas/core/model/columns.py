# coding: utf-8
'''
Column type management and the `Column` class definition. `Column`s are the 
sole definition eagerly exposed by this module. They are accessed as class
properties of `Model`s.

`Column`s are created with a string containing their type definition. The type 
definition is then either resolved as a foreign key or checked against the 
keys of the master type map, which are regular expressions, for a matching 
type. The `ColumnType` of a `Column` is stored in the `type` attribute.
'''

import re
import uuid

from ...exceptions import InvalidSchema
from ...utils import logger
from .ast import Literal, ObjectReference, ILiteral, MAllTypes, Aggregation, \
	OrderItem
from .constraints import ForeignKeyConstraint, PrimaryKeyConstraint, \
	NotNullConstraint, UniquenessConstraint
from .tables import Table
from . import _sentinel

#	Create a log.
log = logger(__name__)

#	Define a meta-null for identifying whether a column default has been 
#	specified.
_meta_null = object()

class ColumnType:
	'''The root column type class.'''

	def __init__(self, lazy):
		'''::lazy Whether this column type is lazy-loaded.'''
		self.lazy = lazy
		self.type = self.input_type = None

	@classmethod
	def resolve(cls, specifier):
		if specifier.startswith('fk:'):
			return ForeignKeyColumnType(specifier[3:])
		for regex, checked_typ in _type_map.items():
			if re.match(regex, specifier):
				return checked_typ
		raise InvalidSchema('Invalid column type specifier %s'%specifier)
	
	def bind(self, column):
		'''
		Finalize the binding onto a host column, once all relevant relationships
		are established.
		'''
		pass

	def describe(self):
		'''Return an SQL serialization of this column type.'''
		raise NotImplementedError()
	
	def get_default(self):
		'''
		Return the default value for this column type, or the sentinel value.
		'''
		return _sentinel

class BasicColumnType(ColumnType):
	'''
	The trivial case of a column type. Instances are assumed to be singleton.
	'''

	def __init__(self, typ, input_type='text', default_policy=None, lazy=False):
		'''
		Create a new basic column type.
		::typ The SQL type of this column.
		::input_type The `<input/>` to use for this column type in forms.
		::default_policy A callable yeilding a default value for this column.
		::lazy Whether `Column`s of this type should be lazy-loaded.
		'''
		super().__init__(lazy)
		self.type, self.input_type = typ, input_type
		self.default_policy = default_policy

	def describe(self):
		return self.type

	def get_default(self):
		'''Return the result of `default_policy` or the sentinel value.'''
		return self.default_policy() if self.default_policy else _sentinel

class ForeignKeyColumnType(ColumnType):
	'''
	A foreign key column type which stores the column to which it refers.
	'''

	def __init__(self, target_ref):
		'''::target_ref A reference specifier of the format <table>.<column>'''
		super().__init__(False)
		self.target_ref = target_ref
		self.target = None

	def bind(self, column):
		'''
		Once relationships are established, resolve the foreign key reference.
		'''
		#	Parse the reference specifier.
		target_table, target_column = self.target_ref.split('.')
		#	Locate the target column.
		for table in Table.instances:
			if table.name != target_table:
				continue
			for check in table.columns.values():
				if check.name == target_column:
					self.target = check
					break
		
		#	Assert a target was found.
		if not self.target:
			raise InvalidSchema('Non-existant foreign key target %s'%(
				self.target_ref
			))

		#	Add a foreign key constraint.
		column.add_constraint(ForeignKeyConstraint(self.target))

	def describe(self):
		'''Return the SQL type of this column (from the target column).'''
		return self.target.type.describe()

#	Define the default type map.
_type_map = {
	'int(?:eger)*': 	BasicColumnType('INTEGER', 'number'),
	'real|float': 		BasicColumnType('REAL'),
	'serial': 			BasicColumnType('SERIAL'),
	'text': 			BasicColumnType('TEXT'),
	'longtext': 		BasicColumnType('TEXT', 'textarea'),
	'bool(?:ean)*':		BasicColumnType('BOOLEAN', 'checkbox'),
	'uuid': 			BasicColumnType('CHAR(32)', 'text', 
							default_policy=uuid.uuid4),
	'pass(?:word)*':	BasicColumnType('TEXT', 'password'),
	'date$': 			BasicColumnType('DATE', 'date'),
	'time$': 			BasicColumnType('TIME', 'time'),
	'dt|datetime':		BasicColumnType('TIMESTAMP', 'datetime-local'),
	'json':				BasicColumnType('JSON', lazy=True)
}

#	TODO: Disable lazy loading argument.
class Column(ObjectReference, ILiteral, MAllTypes):
	'''
	`Column`s are comparable SQL `Node`s that maintain a type and a set of 
	`Constraint`s. In addition to all comparisions, they support the generation
	of `Aggregation`s.
	'''

	def __init__(self, typ, *constraints, default=_meta_null, 
			nullable=True, unique=False, primary_key=False, dictized=True):
		'''
		Create a new column. This should generally be done while defining the
		attribute map of a model within it's decorator.
		::typ The type specifier string.
		::constraints The set of `Constraint`s on this column.
		'''
		super().__init__('COLUMN')
		self.name, self.type = None, ColumnType.resolve(typ)
		self.default = default
		self.dictized = dictized
		self.table = None

		self.constraints = list(constraints)
		#	Define a by-class constraint search
		def contains_instance(cls):
			for constraint in self.constraints:
				if isinstance(constraint, cls):
					log.warning('Duplication of %s constraint; ignoring'%(
						cls.__name__
					))
					return True
			return False
	
		#	Add constraints from keyword arguments
		if primary_key and not contains_instance(PrimaryKeyConstraint):
			self.constraints.append(PrimaryKeyConstraint())
		if not nullable and not contains_instance(NotNullConstraint):
			self.constraints.append(NotNullConstraint())
		if unique and not contains_instance(UniquenessConstraint):
			self.constraints.append(UniquenessConstraint())

	def value_on(self, model):
		'''Return the value on this column on `model`.'''
		return getattr(model, self.name)

	def set_value_on(self, model, value):
		'''Assign `value` to `model` on this column.'''
		setattr(model, self.name, value)

	def bind(self, table):
		'''Perform binding for this column given it's `Table`.'''
		self.table = table
		self.type.bind(self)

	def post_bind(self):
		for constraint in self.constraints:
			constraint.bind(self)

	@property
	def asc(self):
		return OrderItem(self, 'ASC')

	@property
	def desc(self):
		return OrderItem(self, 'DESC')

	def add_constraint(self, constraint):
		'''Add and bind a constraint to this column.'''
		self.constraints.append(constraint)
		constraint.bind(self)

	def apply_to_model(self, model):
		'''
		Apply a default value or the sentinel value to the attribute for this 
		column of `model`.
		'''
		if self.default is _meta_null:
			default = self.type.get_default()
		else:
			if callable(self.default):
				default = self.default()
			else:
				default = self.default
		setattr(model, self.name, default)

	def serialize(self, values=None, name_policy=None):
		'''Serialize a reference to this column.'''
		return '.'.join((self.table.name, self.name))

	def serialize_selection(self):
		return self.serialize()

	def serialize_source(self, values=None):
		'''Serialize the source from which this column is selected.'''
		return self.table.name
	
	def describe(self):
		'''
		Serialize a description of this column, including it's constraints.
		'''
		return ' '.join((
			self.name, self.type.describe(),
			*(constraint.describe() for constraint in self.constraints)
		))

	def max(self):
		'''Return the `MAX` `Aggregation` of this column.'''
		return Aggregation('MAX', self)

	def min(self):
		'''Return the `MIN` `Aggregation` of this column.'''
		return Aggregation('MIN', self)

	def count(self):
		'''Return the `COUNT` `Aggregation` of this column.'''
		return Aggregation('COUNT', self)
	
	def is_one_of(self, *options):
		query = False
		for option in options:
			query = (self == option) | query
		return query.grouped
