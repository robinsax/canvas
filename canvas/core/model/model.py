#	coding utf-8
'''
The base model class definition.
'''

from ...namespace import export
from .columns import Column
from .joins import Join

@export
class Model:

	@classmethod
	def get(cls, reference_value, session):
		query = (cls.__accessors__[0] == reference_value).group()
		for accessor in cls.__accessors__[1:]:
			query = query | (accessor == reference_value).group()
		return session.query(cls, query, one=True)
	
	@classmethod
	def join(cls, *augmentations):
		return Join('INNER', cls, augmentations)

	def __load__(self): pass
	def __create__(self): pass

	def __populate__(self):
		self.__dirty__ = dict()
		for name, column in self.__class__.__schema__.items():
			if isinstance(getattr(self, name), Column):
				setattr(self, name, column.get_default())

	def __setattr__(self, attr, value):
		if attr in self.__class__.__schema__ and attr not in self.__dirty__:
			self.__dirty__[attr] = getattr(self, attr)
		super().__setattr__(attr, value)
