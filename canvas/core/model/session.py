#	coding utf-8
'''
The session class definition.
'''

import inspect

from psycopg2 import (
	IntegrityError, 
	connect
)

from ...exceptions import ValidationErrors
from ...utils import logger
from ...configuration import config
from .columns import _sentinel
from .model import Model
from .joins import Join
from .constraints import get_constraint
from .sql_nodes import SQLAggregatorCall
from .sql_factory import (
	table_creation,
	selection,
	row_creation,
	row_update,
	row_deletion
)

log = logger(__name__)

#	TODO: Allow primary key modification.

class _Session:

	def __init__(self):
		self._connection, self._cursor = None, None		
		self.active_mappings = dict()

	@property
	def connection(self):
		if self._connection is None:
			self._connection = connect(**config.database)

		return self._connection
	
	@property
	def cursor(self):
		if self._cursor is None:
			self._cursor = self.connection.cursor()

		return self._cursor

	def _row_reference(self, model):
		return '%s=>%s'%(
			model.__class__.__table__,
			model.__mapped_as__
		)

	def _map_model(self, model, row):
		i = 0
		for name, column in model.__class__.__schema__.items():
			column.set_value_for(model, row[i])
			i += 1

		model.__dirty__ = dict()
		self._update_reference(model)

	def _update_reference(self, model):
		if hasattr(model, '__mapped_as__'):
			previous = self._row_reference(model)
			if previous in self.active_mappings:
				del self.active_mappings[previous]
		
		model.__mapped_as__ = model.__class__.__primary_key__.value_for(model)
		self.active_mappings[self._row_reference(model)] = model

	def _precheck_constraints(self, model):
		error_dict = dict()
		
		for name, column in model.__class__.__schema__.items():
			to_check = column.value_for(model)
			if to_check == _sentinel:
				continue
			
			for constr in column.constraints:
				try:
					if not constr.check(model, to_check):
						error_dict[name] = constr.error_message
						break
				except NotImplementedError: pass
		
		if len(error_dict) > 0:
			raise ValidationErrors(error_dict)

	def _load_model(self, model_cls, row):
		reference = '%s=>%s'%(model_cls.__table__, row[0])
		
		remap = reference in self.active_mappings
		model = self.active_mappings[reference] if remap else model_cls.__new__(model_cls)
		if not remap:
			model.__dirty__ = dict()
			
		self._map_model(model, row)

		if not remap:
			model.__load__()

		return model

	def _load_joined_model(self, join, row):
		model = self._load_model(join.model_cls, row)

		augmentation_start = len(join.model_cls.__schema__)
		for i, augmentation in enumerate(join.augmentations):
			setattr(model, augmentation.name, row[augmentation_start + i])

		return model

	def execute(self, sql, values=()):
		if config.development.log_emitted_sql:
			log.debug(sql)

			if len(values) > 0:
				log.debug('\t%s'%str(values))
			
		try:
			self.cursor.execute(sql, values)
		except IntegrityError as ex:
			constraint = get_constraint(ex.diag.constraint_name)
			try:
				raise ValidationErrors({
					constraint.column.name: constraint.error_message
				})
			except BaseException as inner_ex:
				if isinstance(inner_ex, ValidationErrors):
					raise inner_ex
				raise ex
		
		return self

	def save(self, model):
		model_cls = model.__class__
		self._precheck_constraints(model)

		self.execute(*row_creation(model))

		self._map_model(model, self.cursor.fetchone())

		model.__create__()
		return self

	def detach(self, model):
		del self.active_mappings[self._row_reference(model)]
		return self

	def delete(self, model):
		self.execute(*row_deletion(model))

		return self.detach(model)

	def query(self, target, conditions=True, one=False, count=None, order_by=None, descending=False, for_update=False, for_share=False):
		if conditions is False:
			return None if one else []
		
		for_ = None
		if for_share:
			for_ = 'SHARE'
		if for_update:
			for_ = 'UPDATE'
		order = (order_by, not descending) if order_by is not None else None		
		self.execute(*selection(target, conditions, order, for_))

		def from_loader_method(loader_method):
			if one:
				row = self.cursor.fetchone()
				if row is None:
					return None

				return loader_method(target, row)
			else:
				result = []
				for i, row in enumerate(self.cursor):
					if count is not None and i >= count:
						break
					result.append(loader_method(target, row))
				return result

		if inspect.isclass(target) and issubclass(target, Model):
			return from_loader_method(self._load_model)
		elif isinstance(target, Join):
			return from_loader_method(self._load_joined_model)
		else:
			if isinstance(target, SQLAggregatorCall):
				one = True
			
			if one:
				return self.cursor.fetchone()
			else:
				return [r[0] for r in self.cursor.fetchall()]

	def _commit_one(self, model):
		if len(model.__dirty__) > 0:
			self._precheck_constraints(model)

			self.execute(*row_update(model))

			self._update_reference(model)
			model.__dirty__ = dict()

	def commit(self, model=None):
		if model is None:
			to_commit = list(self.active_mappings.items())

			for ref, model in to_commit:
				self._commit_one(model)
		else:
			self._commit_one(model)
		
		self.connection.commit()
		return self

	def reset(self):
		self.rollback()
		self.active_mappings = dict()

		return self
	
	def rollback(self, reset_loaded=True):
		if reset_loaded:
			for model in self.active_mappings.values():
				for attr, reset_to in model.__dirty__.items():
					model[attr] = reset_to
			model.__dirty__ = dict()

		if self._connection is not None:
			self._connection.rollback()
			
		return self

	def close(self):
		if self._connection is not None:
			self._connection.close()

		return self

	def __del__(self):
		self.close()
