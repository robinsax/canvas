#	coding utf-8
'''
The base model class definition.
'''

from ...namespace import export
from ..json_io import json_serializer, serialize_json
from .columns import Column
from .joins import Join, Attachment

@export
class Model:

	@classmethod
	def get(cls, reference_value, session):
		query = (cls.__accessors__[0] == reference_value).group()
		for accessor in cls.__accessors__[1:]:
			query = query | (accessor == reference_value).group()
		return session.query(cls, query, one=True)
	
	@classmethod
	def onto(cls, attr_name):
		return Attachment(cls, attr_name)

	@classmethod
	def join(cls, attachment):
		target_cls = attachment.model_cls
		link = from_ = to = None
		
		#	Check if this is many side.
		for column in cls.__schema__.values():
			if column.is_fk and column.reference.model.__table__ == target_cls.__table__:
				link = column
				from_ = cls
				to = target_cls

		#	Check if this is one side.
		for column in target_cls.__schema__.values():
			if column.is_fk and column.reference.model.__table__ == cls.__table__:
				link = column
				from_ = target_cls
				to = cls
		
		if not link:
			raise InvalidQuery('No link between "%s" and "%s"'%(cls.__table__, target_cls.__table__))

		return Join(from_, to, link, attachment.attr_name, from_.__table__ == cls.__table__)

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

@json_serializer(Model)
def serialize_model(model):
	from . import dictize
	
	return dictize(model)
