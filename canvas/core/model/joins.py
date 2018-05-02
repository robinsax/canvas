#	coding utf-8
'''
Joins.
'''

from ...exceptions import InvalidQuery
from ...namespace import export_ext

@export_ext
class Attachment:

	def __init__(self, model_cls, attr_name):
		self.model_cls = model_cls
		self.attr_name = attr_name

@export_ext
class Join:
	
	def __init__(self, source_cls, target_cls, link_column, load_onto, one_side):
		self.source_cls, self.target_cls = source_cls, target_cls
		self.link_column, self.load_onto = link_column, load_onto
		self.one_side = one_side

	def serialize_selection(self):
		selection = []
		for model in (self.source_cls, self.target_cls):
			selection.extend([c.serialize() for c in model.__schema__.values()])
			
		return ', '.join(selection)
	
	def serialize_source(self):
		return ' '.join([
			self.source_cls.__table__, 'JOIN', self.target_cls.__table__,
			'ON', (self.link_column.reference == self.link_column).serialize(tuple())
		])
