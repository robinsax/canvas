#	coding utf-8
'''
ORM class, decorator, and utility definitions. 
'''

from . import psycopg2_extensions

from ..exceptions import ColumnDefinitionError
from ..utils import register

#	The name to class mapping of enumerable types
#	to create and reference in Postgres.
_all_enum = {}

#	Initialize package.
from .columns import (
	Column, 
	ColumnType, 
	ForeignKeyColumnType, 
	EnumColumnType
)
from .constraints import *
from .session import Session
from .sql_factory import table_creation, enum_creation

#	Declare exports.
__all__ = [
	#	Decorators.
	'schema',
	'enum',
	#	Interaction points and utilities.
	'create_session',
	'create_everything',
	'dictize',
	'dictize_all',
	#	Columns.
	'Column',
	#	Constraints.
	'Constraint',
	'RegexConstraint',
	'UniquenessConstraint',
	#	Column types.

]

#	Declare documentation targets.
__doc_items__ = [
	#	Decorators.
	'schema',
	'enum',
	#	Interaction points and utilities.
	'create_session',
	'create_everything',
	'dictize',
	'dictize_all',
	#	Session.
	'session',
	#	Columns.
	'Column',
	#	Constraints.
	'Constraint',
	'RegexConstraint',
	'UniquenessConstraint',
	#	Column types.
	'ColumnType',
	'ForeignKeyColumnType',
	'EnumColumnType'
]

#	TODO: Encode column defaults into SQL when possible.

class _ColumnIterator:
	'''
	An ordered iterator on the columns of a model class.
	
	The nature of this object is not exposed outside of 
	this package.
	'''

	def __init__(self, model_cls, yield_i):
		'''
		Create a column iterator.

		:model_cls The mapped model class.
		:yield_i Whether the current index should be included 
			in the yielded tuple as a third argument.
		'''
		self.model_cls = model_cls
		self.yield_i = yield_i
		self.stop = len(model_cls.__columns__)
		self.i = 0

	def __iter__(self):
		return self

	def __next__(self):
		if self.i >= self.stop:
			#	No more columns.
			raise StopIteration()
		
		#	Read the current column.
		name = self.model_cls.__columns__[self.i]
		column = self.model_cls.__schema__[name]

		#	Increment position
		self.i += 1

		if self.yield_i:
			#	Yield with index.
			return name, column, self.i - 1
		else:
			#	Yield without index.
			return name, column

#	The table name to model class mapping.
_all_orm = {}
def schema(table_name, schema, accessors=[]):
	'''
	The model class mapping and schema declaration 
	decorator.

	Decorated classes will be added to this package's
	namespace after pre-initialization.

	:table_name The name of the SQL table for this model 
		class.
	:schema A column name to column definition mapping.
	:accessors A list of column names which are checked for
		equality by the `get(reference, session)` classmethod.
	'''
	def wrap(cls):
		#	Populate column attributes and add the
		#	columns to the class.
		for name, col in schema.items():
			col.name = name
			col.model = cls
			setattr(cls, name, col)

		#	Define placeholder callbacks if real implementations
		#	aren't present so their existance can be assumed.
		if getattr(cls, '__on_load__', None) is None:
			cls.__on_load__ = lambda self: None
		if getattr(cls, '__on_create__', None) is None:
			cls.__on_create__ = lambda self: None
		
		#	Assert the existance of a single primary key column
		#	for this model class and find that column
		primary_key = None
		for col_name, col_obj in schema.items():
			if col_obj.primary_key:
				if primary_key is not None:
					#	We already found one.
					raise ColumnDefinitionError(f'Multiple primary keys for table {table_name}')
				#	Save the column object.
				primary_key = col_obj

		if primary_key is None:
			#	No primary key specified.
			raise ColumnDefinitionError(f'No primary key for table {table_name}')
		
		#	Add the model class to the global ORM mapping.
		_all_orm[table_name] = cls

		#	Populate class attributes.
		cls.__table__ = table_name
		cls.__schema__ = schema
		#	Define a fixed order on columns for use in SQL serialization.
		cls.__columns__ = sorted(schema.keys(), key=lambda n: schema[n].primary_key, reverse=True)
		cls.__primary_key__ = primary_key
		#	Define a dirty-checking flag for simple pre-insert
		#	necessity checks.
		cls.__dirty__ = False
		cls.__accessors__ = [schema[name] for name in accessors]

		#	Create a `get()` class method for easy single-item 
		#	retrieval.
		def get(cls, val, session):
			query = (cls.__accessors__[0] == val).group()
			for accessor in cls.__accessors__[1:]:
				query = query | (accessor == val).group()
			return session.query(cls, query, one=True)
		cls.get = classmethod(get)

		#	Wrap initialization so that after instantiation (i.e. 
		#	when a new instance/row is being created) columns are
		#	guarenteed to be populated.
		inner_init = cls.__init__
		def init(self, *args, **kwargs):
			for name, column in cls.__schema__.items():
				setattr(self, name, column.get_default())
			inner_init(self, *args, **kwargs)
		cls.__init__ = init

		#	Override `__setattr__` to set the `__dirty__` flag 
		#	when a column value is set.
		inner_set = cls.__setattr__
		def set_with_check(self, attr, val):
			if attr in self.__columns__:
				#	This attribute is mapped to a column; in-memory
				#	version is now dirty.
				inner_set(self, '__dirty__', True)
			inner_set(self, attr, val)
		cls.__setattr__ = set_with_check

		#	Create a ordered column iterator class method.
		def schema_iter(cls, i=False):
			return _ColumnIterator(cls, i)
		cls.schema_iter = classmethod(schema_iter)

		#	Register the model class for namespace management.
		register.model(cls)
		
		return cls
	return wrap

def enum(name):
	'''
	The enumerable type model declaration decorator.

	Decorated enums will be added to this package's
	namespace after pre-initialization.

	:name A unique name for the enumerable type declaration
		in Postgres.
	'''
	def wrap(cls):
		cls.__type_name__ = name
		
		#	Add to name to enumerable class mapping.
		_all_enum[name] = cls
		return cls
	return wrap

def dictize(model_obj, omit=[]):
	'''
	Return a dictionary containing a column name, column 
	value mapping for `model_obj`.

	:model_obj The model class instance to dictize.
	:omit A list of columns not to include in the returned
		dictionary.
	'''
	return {
		name: getattr(model_obj, name, None) for name in model_obj.__class__.__columns__ if name not in omit
	}

def dictize_all(model_list, omit=[]):
	'''
	Return a list containing dictizations of all the model
	objects in `model_list`.

	:model_list A list of model class instances to dictize.
	:omit A list of columns not to include in the returned
		dictionaries.
	'''
	return [dictize(model, omit) for model in model_list]
	
def create_session():
	'''
	Create a database session. `Session` generation should
	always use this function to allow future modifications
	to the `Session` constructor.
	'''
	return Session()

def create_everything():
	'''
	Resolve foreign keys and enum references then issue table 
	and enumarable type creation SQL.
	'''
	#	Resolve foreign keys.
	for table, model_cls in _all_orm.items():
		for col_name, col_obj in model_cls.schema_iter():
			if not isinstance(col_obj.type, ForeignKeyColumnType):
				#	No foreign key to resolve.
				continue
			
			#	Parse reference.
			try:
				dest_table_name, dest_col_name = col_obj.reference.split('.')
			except:
				raise ColumnDefinitionError(f'Malformed foreign key declaration: {col_obj.reference}')

			#	Assert reference validity.
			if dest_table_name not in _all_orm:
				#	The referenced table does not exist.
				raise ColumnDefinitionError(f'Invalid foreign key {col_obj.reference}: No such table')
			dest_schema = _all_orm[dest_table_name].__schema__
			if dest_col_name not in dest_schema:
				#	The referenced column does not exist.
				raise ColumnDefinitionError(f'Invalid foreign key {col_obj.reference}: No such column')

			#	Store the reference in the column.
			col_obj.reference = dest_schema[dest_col_name]

	#	Create a database session for table and type creation.
	session = create_session()

	#	Issue type creation.
	for name, enum in _all_enum.items():
		session.execute(*enum_creation(enum))
	
	#	Issue table creation.
	for tn, model in _all_orm.items():
		session.execute(*table_creation(model))
	
	#	Commit the transaction.
	session.commit()
