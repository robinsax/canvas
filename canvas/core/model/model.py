#	coding utf-8
'''
The base `Model` class and `model` decorator definitions. Inheritance over
`Model` occurs implicitly when the model decorator is used.
'''

from .tables import Table

class Model:
	'''
	The base model class implements session, dirty attribute, and lazy-load 
	tracking as well as several convenience methods.
	'''
	#	Ensure these exist in the MRO.
	__table__ = __session__ = __dirty__ = None

	@classmethod
	def join(cls, other, condition=None):
		return cls.__table__.join(other, condition)

	def __loaded__(self, session):
		'''A callback invoked immediatly after a model is loaded.'''
		self.__dirty__ = dict()
		self.__session__ = session

	def __getattribute__(self, key):
		'''Retrieve lazy-loaded attributes from the database when accessed.'''
		table = super().__getattribute__('__class__').__table__
		if super().__getattribute__('__session__') and key in table.columns:
			row_access = super().__getattribute__(table.primary_key.name)
			exec_statement(
				SelectStatement(table.columns[key], table.primary_key == row_access)
			)
			return 'TODO'

		return super().__getattribute__(key)

	def __setattr__(self, key, value):
		'''Set the dirty flag for in-schema attributes when assigned.'''
		if key in self.__table__.columns:
			if key not in self.__dirty__:
				self.__dirty__[key] = value

		return super().__setattr__(key, value)
	
def model(table_name, contents):
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
		#	Create and bind a table.
		Table(table_name, contents).bind(_Model)

		return _Model
	return model_inner
