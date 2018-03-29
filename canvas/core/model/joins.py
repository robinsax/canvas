#	coding utf-8
'''
Join object definition.
'''

#	TODO: Make augmented column writable

from ...exceptions import InvalidQuery
from ...namespace import export_ext

@export_ext
class Join:

	def __init__(self, typ, model_cls, augmentations):
		self.type = typ
		self.model_cls = model_cls
		self.augmentations = augmentations

		if len(augmentations) == 0:
			raise InvalidQuery('Not a join')
		
		target_model_columns = self.augmentations[0].model.__schema__.values()
		self.link_column = None
		for column in self.model_cls.__schema__.values():
			if column.is_fk and column.reference in target_model_columns:
				self.link_column = column
				break
		if self.link_column is None:
			raise InvalidQuery('Cannot link augumented columns to %s'%model_cls.__class__.__table__)

	def serialize_selection(self):
		#   Damn check that out...                                                              v
		column_references = [column.serialize() for column in self.model_cls.__schema__.values()]
		column_references += [augumentation.serialize() for augumentation in self.augmentations]
		return ', '.join(column_references)

	def serialize_source(self):
		return ' '.join([
			self.model_cls.__table__, 
			self.type, 'JOIN', 
			self.link_column.reference.model.__table__,
			'ON', self.link_column.serialize(), '=', self.link_column.reference.serialize()
		])
