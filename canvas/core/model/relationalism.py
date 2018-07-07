# coding: utf-8
'''
Relational property API.
'''

from .ast import nodeify
from .dictizations import dictized_property
from .columns import ForeignKeyColumnType

_meta_null = object()

class RelationSpec:
	instance_map = dict()

	def __init__(self, cls_name, attr, target, condition=True, order=None):
		self.attr = attr
		self.target_gen, self.condition = lambda: target(None).__table__, nodeify(condition)
		self.order = order

		RelationSpec.instance_map[''.join((cls_name, attr))] = self

	@classmethod
	def get(cls, cls_name, attr):
		return cls.instance_map.get('__'.join((cls_name, attr)))

	#	TODO: Copied from joins... golf!
	#	Also should be resolved at create time.
	def find_link_column(self, source):
		source_columns = source.get_columns()
		dest_columns = self.target_gen().get_columns()

		#	Check the source.
		for column in source_columns:
			typ = column.type
			if not isinstance(typ, ForeignKeyColumnType):
				continue
			for check_column in dest_columns:
				if check_column is typ.target:
					return column, False		

		#	Check the destination.
		for column in dest_columns:
			typ = column.type
			if not isinstance(typ, ForeignKeyColumnType):
				continue
			for check_column in source_columns:
				if check_column is typ.target:
					return column, True

def relational_property(*args, **kwargs):
	def relational_property_inner(meth):
		safe_key = ''.join(('__', meth.__name__))
		cls_name = meth.__qualname__.split('.')[-2]

		relation_spec = RelationSpec.get(cls_name, safe_key)
		if not relation_spec:
			relation_spec = RelationSpec(cls_name, safe_key, meth)

		def meth_replacement(self):
			existing = getattr(self, safe_key, _meta_null)
			if existing is not _meta_null:
				return existing
			else:
				table = self.__class__.__table__
				link, one_to_many = relation_spec.find_link_column(table)

				if one_to_many:
					cond = relation_spec.condition & (link == link.type.target.value_on(self))
				else:
					cond = relation_spec.condition & (link.type.target == link.value_on(self))

				result = self.__session__.query(relation_spec.target_gen(), 
						cond,
						order=relation_spec.order, one=not one_to_many)
				setattr(self, safe_key, result)
				return result

		meth_replacement.__name__ = meth.__name__
		
		if kwargs.get('dictized', False):
			return dictized_property(meth_replacement)
		return property(meth_replacement)
	
	if kwargs:
		return relational_property_inner
	return relational_property_inner(args[0])
