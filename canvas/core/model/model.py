#	coding utf-8
'''
The base model class definition.
'''

from ...namespace import export
from .columns import Column

@export
class Model:

	@classmethod
	def get(cls, reference_value, session):
		query = (cls.__accessors__[0] == val).group()
		for accessor in cls.__accessors__[1:]:
			query = query | (accessor == val).group()
		return session.query(cls, query, one=True)
	
	def __on_load__(self):
		pass

	def __on_create__(self):
		pass

	def __label__(self, session):
		return self.id

	def __populate__(self):
		for name, column in self.__class__.__schema__.items():
			if isinstance(getattr(self, name), Column):
				setattr(self, name, column.get_default())

	def __setattr__(self, attr, value):
		if attr in self.__class__.__schema__ and attr not in self.__dirty__:
			self.__dirty__[attr] = getattr(self, attr)
		super().__setattr__(attr, value)
