#	coding utf-8
'''
ORM
'''

#	TODO: Required by .columns but shouldn't live here
_all_enum = {}

from ..exceptions import ColumnDefinitionError
from ..utils import register
from .columns import Column, ColumnType, ForeignKeyColumnType, EnumColumnType
from .constraints import *
from .session import Session
from .sql_factory import table_creation, enum_creation

__all__ = [
	'schema',
	'create_session',
	'create_everything',
	'Column',
	'Constraint',
	'RegexConstraint',
	'UniquenessConstraint'
]

#	TODO: Encode default into SQL when possible
#	TODO: Comments

class ColumnIterator:

	def __init__(self, model_cls, yield_i):
		self.model_cls = model_cls
		self.yield_i = yield_i
		self.stop = len(model_cls.__columns__)
		self.i = 0

	def __iter__(self):
		return self

	def __next__(self):
		if self.i >= self.stop:
			raise StopIteration()
		name = self.model_cls.__columns__[self.i]
		column = self.model_cls.__schema__[name]
		i = self.i
		self.i += 1
		if self.yield_i:
			return (name, column, i)
		else:
			return (name, column)

_all_orm = {}
def schema(table_name, schema, accessors=[]):
	def wrap(cls):
		for name, col in schema.items():
			col.name = name
			col.model = cls
			setattr(cls, name, col)

		#	Placeholder callbacks
		if getattr(cls, '__on_load__', None) is None:
			cls.__on_load__ = lambda self: None
		if getattr(cls, '__on_create__', None) is None:
			cls.__on_create__ = lambda self: None
		
		pk = None
		for col_name, col_obj in schema.items():
			if col_obj.primary_key:
				if pk is not None:
					raise ColumnDefinitionError(f'Multiple primary keys for table {table_name}')
				pk = col_obj
		if pk is None:
			raise ColumnDefinitionError(f'No primary key for table {table_name}')
		
		_all_orm[table_name] = cls
		cls.__table__ = table_name
		cls.__schema__ = schema
		#	Gives us a fixed order for column names, with primary key first
		cls.__columns__ = sorted(schema.keys(), key=lambda n: schema[n].primary_key, reverse=True)
		cls.__primary_key__ = pk

		#	Create accessors TODO: Use to make indicies
		accessors_objs = [schema[name] for name in accessors]
		cls.__accessors__ = accessors_objs

		#	Create a get class method
		def get(cls, val, session):
			query = (cls.__accessors__[0] == val).group()
			for accessor in cls.__accessors__[1:]:
				query = query | (accessor == val).group()
			return session.query(cls, query, one=True)
		cls.get = classmethod(get)

		#	Override init. to populate fields
		inner = cls.__init__
		def init(self, *args, **kwargs):
			for name, column in cls.__schema__.items():
				setattr(self, name, column.get_default())
			inner(self, *args, **kwargs)
		cls.__init__ = init

		#	Create a ordered column iterator
		def schema_iter(cls, i=False):
			return ColumnIterator(cls, i)
		cls.schema_iter = classmethod(schema_iter)

		register('model')(cls)
		
		return cls
	return wrap

def enum(name):
	'''
	Define and register the model of the decorated
	enumerable type declaration

	TODO: Some kind of dynamic packaging for enums (to model?)
	'''
	def wrap(cls):
		cls.__type_name__ = name
		
		#	Register
		_all_enum[name] = cls
		return cls
	return wrap

def dictize(model_obj, omit=[]):
	return {
		name: getattr(model_obj, name, None) for name in model_obj.__class__.__columns__ if name not in omit
	}

def dictize_all(model_list, omit=[]):
	return [dictize(model, omit) for model in model_list]
	
def create_session():
	return Session()

def create_everything():
	#	Resolve foreign keys
	for table, m_cls in _all_orm.items():
		for c_name, c_obj in m_cls.__schema__.items():
			if not isinstance(c_obj.type, ForeignKeyColumnType):
				continue
			
			dest_table_n, dest_col_n = c_obj.reference.split('.')
			if dest_table_n not in _all_orm:
				raise ColumnDefinitionError(f'Invalid foreign key {c_obj.reference}: No such table')
			dest_schema = _all_orm[dest_table_n].__schema__
			if dest_col_n not in dest_schema:
				raise ColumnDefinitionError(f'Invalid foreign key {c_obj.reference}: No such column')

			referenced = dest_schema[dest_col_n]
			c_obj.reference = referenced

	session = create_session()

	#	Create types
	for name, enum in _all_enum.items():
		session.execute(*enum_creation(enum))
	
	#	Create tables	
	for tn, model in _all_orm.items():
		session.execute(*table_creation(model))
	session.commit()
