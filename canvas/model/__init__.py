#	coding utf-8
'''
ORM class, decorator, and utility definitions. 
'''

from ..exceptions import (
	ColumnDefinitionError,
	InvalidSchema
)
from ..utils import register

#	Initialize type adaption first.
from .type_adaption import *

##########################
#	TODO: Refactor.
#	The name to class mapping of enumerable types to create and reference in 
#	Postgres.
_all_enum = {}
#	The table name to model class mapping.
_all_orm = {}

#	An exception used by foreign key columns to cause another table to be 
#	resolved first. Not exposed.
class _PushResolveNow(Exception):

	def __init__(self, table):
		self.table = table
###########################

#	Initialize package.
from .columns import (
	Column, 
	ColumnType, 
	ForeignKeyColumnType, 
	EnumColumnType
)
from .constraints import *
from .session import _Session
from .sql_factory import *

#	Declare exports.
__all__ = [
	#	Decorators.
	'schema',
	'enum',
	'adapter',
	#	Interaction points and utilities.
	'create_session',
	'create_everything',
	'dictize',
	'dictize_all',
	#	Classes.
	'_Session',
	'Column',
	'Constraint',
	'RegexConstraint',
	'UniquenessConstraint',
	'ColumnType',
	'ForeignKeyColumnType',
	'EnumColumnType',
	'TypeAdapter',
	'SQLExpression',
	'SQLComparison',
	'SQLAggregatorCall'
]

#	TODO: Encode column defaults into SQL when possible.

class _ColumnIterator:
	'''
	An ordered iterator on the columns of a model class.
	
	The nature of this object is not exposed outside of this package.
	'''

	def __init__(self, model_cls, yield_i):
		'''
		Create a column iterator.

		:model_cls The mapped model class.
		:yield_i Whether the current index should be included in the yielded 
			tuple as a third argument.
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

		#	Increment position.
		self.i += 1

		if self.yield_i:
			#	Yield with index.
			return name, column, self.i - 1
		else:
			#	Yield without index.
			return name, column

def _wipe():
	'''
	Wipe the ORM. Should only be called by unit tests.
	'''
	global _all_orm
	_all_orm = {}

def schema(table_name, schema, accessors=None):
	'''
	The model class mapping and schema declaration decorator.

	Decorated classes will be added to this package's namespace after 
	pre-initialization.

	:table_name The name of the SQL table for this model class.
	:schema A column name to column definition mapping.
	:accessors A list of column names which are checked for equality by the 
		`get(reference, session)` classmethod.
	'''
	def wrap(cls):
		#	Place columns.
		for name, col in schema.items():
			#	Populate column attributes.
			col.name = name
			col.model = cls
			#	Add the column as a model class attribute.
			setattr(cls, name, col)

		#	Attach placeholder callbacks if real implementations aren't present 
		#	so their existance can be assumed.
		eat_call = lambda s: None
		if not hasattr(cls, '__on_load__'):
			cls.__on_load__ = eat_call
		if not hasattr(cls, '__on_create__'):
			cls.__on_create__ = eat_call
		
		#	Assert the existance of a single primary key column for this model 
		#	class and find that column.
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
		
		#	Populate class attributes.
		cls.__table__ = table_name
		cls.__schema__ = schema
		cls.__primary_key__ = primary_key
		#	Define a fixed order on columns for use in SQL serialization.
		cls.__columns__ = sorted(schema.keys(), key=lambda n: schema[n].primary_key, reverse=True)
		#	Initialize the rapid dirty-checking flag.
		cls.__dirty__ = False
		#	Initialize the table-existance flag
		cls.__created__ = False

		if accessors is None:
			#	Make the primary key the sole accessor
			cls.__accessors__ = [primary_key]
		else:
			cls.__accessors__ = [schema[name] for name in accessors]

		#	Create a `get()` class method for easy single-item retrieval.
		def get(cls, val, session):
			#	Create query.
			query = (cls.__accessors__[0] == val).group()
			for accessor in cls.__accessors__[1:]:
				query = query | (accessor == val).group()

			#	Execute and return.
			return session.query(cls, query, one=True)
		cls.get = classmethod(get)

		#	Create an ordered shema iterator as a class method.
		def schema_iter(cls, i=False):
			return _ColumnIterator(cls, i)
		cls.schema_iter = classmethod(schema_iter)

		#	Wrap initialization so that after instantiation (i.e. when a new 
		#	instance/row is being created) columns are guarenteed to be 
		#	populated.
		inner_init = cls.__init__
		def init(self, *args, **kwargs):
			#	Invoke standard init.
			inner_init(self, *args, **kwargs)

			#	Populate unset fields.
			for name, column in cls.schema_iter():
				if isinstance(getattr(self, name), Column):
					setattr(self, name, column.get_default())
		cls.__init__ = init

		#	Override `__setattr__` to set the `__dirty__` flag when a column 
		#	value is set.
		inner_set = cls.__setattr__
		def set_with_check(self, attr, val):
			if attr in self.__columns__:
				#	This attribute is mapped to a column; in-memory version is 
				#	now dirty.
				print('DIRTY', self.__table__, attr)
				inner_set(self, '__dirty__', True)
			inner_set(self, attr, val)
		cls.__setattr__ = set_with_check

		#	Add to the global object to table mapping.
		_all_orm[table_name] = cls
		#	Register for access by namespace management.
		register.model(cls)

		return cls
	return wrap

def enum(name):
	'''
	The enumerable type model declaration decorator.

	Decorated enums will be added to this package's namespace after 
	pre-initialization.

	:name A unique name for the enumerable type declaration in Postgres.
	'''
	def wrap(cls):
		cls.__type_name__ = name
		
		#	Add to name to enumerable class mapping.
		_all_enum[name] = cls
		return cls
	return wrap

def dictize(model_obj, omit=[]):
	'''
	Return a dictionary containing a column name, column value mapping for 
	`model_obj`.

	:model_obj The model class instance to dictize.
	:omit A list of columns not to include in the returned dictionary.
	'''
	return {
		name: getattr(model_obj, name, None) for name in model_obj.__class__.__columns__ if name not in omit
	}

def dictize_all(model_list, omit=[]):
	'''
	Return a list containing dictizations of all the model objects in 
	`model_list`.

	:model_list A list of model class instances to dictize.
	:omit A list of columns not to include in the returned dictionaries.
	'''
	return [dictize(model, omit) for model in model_list]
	
def create_session():
	'''
	Create a database session. `_Session` generation should always use this 
	function to allow future modifications to the `_Session` constructor.
	'''
	return _Session()

def create_everything():
	'''
	Resolve foreign keys and enum references then issue table and enumarable 
	type creation SQL.
	'''

	#	Create a database session for table and type creation.
	session = create_session()

	#	Issue type creation.
	for name, enum in _all_enum.items():
		session.execute(*enum_creation(enum))

	#	Create model class state trackers to ensure the foreign key enforced
	#	ordering is both possible and followed.
	_started = []
	def create_model_and_table(model_cls):
		'''
		Finalize a model class and create the corresponding table.
		'''
		if model_cls.__created__:
			#	Already created.
			return
		elif model_cls in _started:
			#	A loop occurred.
			raise InvalidSchema(f'Dependency back-reference for {model_cls.__name__}')
		
		#	Add to started list so reference loops can be caught.
		_started.append(model_cls)

		#	Resolve columns.
		for col_name, col_obj in model_cls.schema_iter():
			try:
				col_obj.resolve(model_cls)
			except _PushResolveNow as recurser:
				create_model_and_table(recurser.table)
				col_obj.resolve(model_cls)

		#	Execute the table creation.
		session.execute(*table_creation(model_cls))

		#	Mark as finished to allow reference.
		model_cls.__created__ = True
	
	for name, model_cls in _all_orm.items():
		create_model_and_table(model_cls)

	#	Commit the transaction.
	session.commit()
