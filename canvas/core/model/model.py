# coding: utf-8
'''
The base `Model` class and `model` decorator definitions. Inheritance over
`Model` occurs implicitly when the model decorator is used.
'''

from ...exceptions import NotFound
from .tables import Table
from .columns import Column
from .dictizations import resolve_dictized_properties
from .relationalism import RelationSpec

class Model:
	'''
	The base model class implements session, dirty attribute, and lazy-load 
	tracking as well as several convenience methods.
	'''
	#	Ensure these exist in the MRO.
	__table__ = __session__ = __dirty__ = None

	@classmethod
	def join(cls, other, condition=True, attr=None):
		return cls.__table__.join(other, condition, attr)

	@classmethod
	def rest_get(cls, pk_val, session):
		instance = cls.get(pk_val, session)
		if not instance:
			raise NotFound(pk_val)
		return instance

	@classmethod
	def with_relation(cls, relation):
		rel_spec = RelationSpec.get(cls.__name__, relation)
		#	TODO: Unsupport order?
		return cls.join(
			rel_spec.target_gen(), 
			rel_spec.condition,
			attr=rel_spec.attr
		)

	@classmethod
	def get(cls, pk_val, session):
		return session.query(cls, cls.__table__.primary_key == pk_val, one=True)

	def __loaded__(self, session):
		'''A callback invoked immediatly after a model is loaded.'''
		self.__dirty__ = dict()
		self.__session__ = session

	def __getattribute__(self, key):
		'''Retrieve lazy-loaded attributes from the database when accessed.'''
		#	TODO: Clean this up its a shitshow.
		table = super().__getattribute__('__class__').__table__
		must_load = (
			super().__getattribute__('__session__') and 
			key in table.columns and 
			isinstance(super().__getattribute__(key), Column)
		)
		if must_load:
			row_access = super().__getattribute__(table.primary_key.name)
			value = self.__session__.query(
				table.columns[key], 
				table.primary_key == row_access, 
				one=True
			)
			setattr(self, key, value)
			return value

		return super().__getattribute__(key)

	def __setattr__(self, key, value):
		'''Set the dirty flag for in-schema attributes when assigned.'''
		if key in self.__table__.columns:
			if key not in self.__dirty__:
				existing = super().__getattribute__(key)
				if not isinstance(existing, Column) and value != existing:
					self.__dirty__[key] = value

		return super().__setattr__(key, value)

def model(table_name, contents, dictized=tuple()):
	'''
	The `model` class decorator is used to define properties of a model class.
	::table_name The name of the table in which to store instances of this 
		model.
	::contents A dictionary containing the name, column or constraint pairs 
		that define the schema of the model.
	'''
	def model_inner(cls):
		#	Patch the type to extend Model.
		_Model = type(cls.__name__, (cls, Model), dict())
		_Model.__dictized__ = list(dictized)
		resolve_dictized_properties(_Model)
		#	Create the table.
		table = Table(table_name, contents)

		#	Override __init__ to assign default or sentinel values.
		inner_init = _Model.__init__
		def init_wrap(self, *args, **kwargs):
			self.__dirty__ = dict()
			for column in table.columns.values():
				column.apply_to_model(self)
			inner_init(self, *args, **kwargs)
		_Model.__init__ = init_wrap

		#	Bind the table.
		table.bind(_Model)

		return _Model
	return model_inner
