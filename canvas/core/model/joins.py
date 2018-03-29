#	coding utf-8
'''
Join object definition.
'''

#	TODO: Make augmented column writable

from ...exceptions import InvalidQuery
from ...namespace import export_ext

class _JoinInstance:

	def __init__(self, target_model, link_column):
		self.target_model, self.link_column = target_model, link_column
		self.columns = []

	def serialize(self):
		return ' '.join([
			'JOIN', self.target_model.__table__,
			'ON', self.link_column.serialize(), '=', self.link_column.reference.serialize()
		])

#	TODO: This is really only an inner join I think.
@export_ext
class Join:

	def __init__(self, typ, model_cls, augmentations):
		self.type = typ
		self.model_cls = model_cls
		self.augmentations = augmentations

		if len(augmentations) == 0:
			raise InvalidQuery('Not a join')
		
		self.join_instances = dict()
		for column in self.augmentations:
			table = column.model.__table__
			target_model_columns = column.model.__schema__.values()

			if table not in self.join_instances:
				link_column = None
				for check_column in self.model_cls.__schema__.values():
					if check_column.is_fk and check_column.reference in target_model_columns:
						link_column = check_column
						break
				if link_column is None:
					raise InvalidQuery('No direct link to %s'%table)

				self.join_instances[table] = _JoinInstance(column.model, link_column)

			self.join_instances[table].columns.append(column)

	def serialize_selection(self):
		column_references = [column.serialize() for column in self.model_cls.__schema__.values()]
		column_references += [augmentation.serialize() for augmentation in self.augmentations]
		return ', '.join(column_references)

	def serialize_source(self):
		return '%s %s'%(
			self.model_cls.__table__,
			' '.join([i.serialize() for i in self.join_instances.values()])
		)
