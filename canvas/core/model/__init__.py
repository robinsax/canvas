#	coding utf-8
'''
ORM class, decorator, and utility definitions. 
'''

from collections import OrderedDict

class _ResolveOther(Exception):

	def __init__(self, table):
		self.table = table

_object_relational_map = dict()

from ...exceptions import InvalidSchema
from ...namespace import export, export_ext
from ...utils import patch_type
from ..request_context import RequestContext
from .model import Model
from .columns import define_column_types
from .sql_factory import table_creation
from .session import _Session


@export_ext
def wipe_orm(are_you_sure=False):
	global _all_orm
	if are_you_sure:
		_all_orm = dict()

@export
def model(table_name, schema, accessors=None):
	def model_wrap(cls):
		#	Resolve primary key and name columns.
		primary_key = None
		for name, column in schema.items():
			if column.primary_key:
				if primary_key:
					raise InvalidSchema('Multiple primary keys for table: %s'%table)
				primary_key = column
			
			column.name, column.model = name, cls
			setattr(cls, name, column)
		if not primary_key:
			raise InvalidSchema('No primary key for table: %s'%table_name)

		#	Order schema by primary key.
		ordered_schema = OrderedDict()
		for key in sorted(schema.keys(), key=lambda n: schema[n].primary_key, reverse=True):
			ordered_schema[key] = schema[key]

		#	Assign some attrs.
		cls.__table__ = table_name
		cls.__schema__ = ordered_schema
		cls.__primary_key__ = primary_key
		cls.__created__ = False
		cls.__accessors__ = [primary_key] if accessors is None else [schema[name] for name in accessors]
		
		inner_init = cls.__init__
		def init_wrap(self, *args, **kwargs):
			self.__populate__()
			self.__dirty__ = dict()
			inner_init(self, *args, **kwargs)
		cls.__init__ = init_wrap

		patched = patch_type(cls, Model)
		_object_relational_map[table_name] = patched
		return patched
	return model_wrap

@export
def dictize(target, omit=[]):
	if isinstance(target, (list, tuple)):
		return [dictize(item) for item in target]
	
	return {
		name: getattr(target, name, None) for name in target.__class__.__columns__ if name not in omit
	}

@export
def create_session():
	return _Session()

@export_ext
def get_some_session():
	context = RequestContext.get()
	if context:
		return context.session
	return create_session()

def create_object_relational_mapping():
	session = create_session()

	started = []
	def create_model_and_table(model_cls):
		if model_cls.__created__:
			return
		elif model_cls in started:
			raise InvalidSchema('Foreign key back-reference for %s'%model_cls.__name__)
		
		started.append(model_cls)

		for name, column in model_cls.__schema__.items():
			try:
				column.resolve()
			except _ResolveOther as recurser:
				create_model_and_table(recurser.table)
				column.resolve(model_cls)

		session.execute(*table_creation(model_cls))
		model_cls.__created__ = True
	
	for name, model_cls in _object_relational_map.items():
		create_model_and_table(model_cls)

	session.commit()

def initialize_model():
	define_column_types()
	create_object_relational_mapping()
