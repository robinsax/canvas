#	coding utf-8
'''
The `Session` class definition.
'''

import inspect

from psycopg2 import IntegrityError, connect

from ...exceptions import ValidationErrors
from ...configuration import config
from . import _sentinel

class Session:
	'''
	The `Session` class is used for database interaction and, transparently, 
	model management. Request context's contain a `Session` by default. 
	'''

	def __init__(self):
		'''Create a new session.'''
		self._connection = self._cursor = None
		self.loaded_models = dict()

	@property
	def connection(self):
		'''The connection property allowing lazy actualization.'''
		if not self._connection:
			#	Create the connection.
			self._connection = connect(
				database=	config.database.database,
				user=		config.database.user,
				password=	config.database.password,
				host=		config.database.host
			)
		
		return self._connection
	
	@property
	def cursor(self):
		'''The cursor property allowing lazy actualization.'''
		if not self._cursor:
			self._cursor = self.connection.cursor()

		return self._cursor

	def assign_row_to_model(self, model, row_segment):
		'''Assign `model` with the values contained in `row_segment`.'''
		#	Assign column values.
		table = model.__class__.__table__
		for i, column in enumerate(table.get_columns()):
			setattr(model, column.name, row_segment[i])

		#	Invoke load callback.
		model.__loaded__(self)

	def precheck_constraints(self, model):
		'''
		Precheck all constraints in the schema of `model` for violations,
		raising an `UnprocessableEntity` exception if any exist.
		'''
		error_dict, error_summary = dict(), None
		table = model.__class__.__table__

		#	Check column level constraints
		for column in table.columns.values():
			value = getattr(model, column.name)
			if value is _sentinel:
				#	The model was just created and this attribute hasn't been 
				#	initialized yet.
				continue
			
			#	Check this column's constraints.
			for constraint in column.constraints:
				try:
					if constraint.precheck_violation(model, value):
						error_dict[name] = constraint.error_message
						break
				except NotImplementedError:
					pass
		
		#	Check table level constraints.
		for constraint in table.constraints:
			try:
				if constraint.precheck_violation(model, value):
					error_summary = constraint.error_message
					break
			except NotImplementedError:
				pass

		if error_dict or error_summary:
			#	Violations were found.
			raise ValidationErrors(error_dict, error_summary)

	def load_model_instance(self, model_cls, row_segment):
		'''Load an instance of `model_cls` from `row_segment`.'''
		#	Create a row reference for this row and check if a model is 
		#	already loaded for that row.
		row_reference = '=>'.join((model_cls.__table__.name, row[0]))
		is_remap = row_reference in self.loaded_models

		if is_remap:
			#	Re-use the existing model.
			model = self.loaded_models[row_reference]
		else:
			#	Backdoor a new instance.
			model = model_cls.__new__(model_cls)
		
		#	Assign the values and return.
		self.assign_row_to_model(model, row_segment)
		return model

	def _load_join(self, join, one):		
		first_cols = len(join.source_cls.__schema__)
		attr_name = join.load_onto

		def load_one(row):
			#	Load a single instance of each, childing and returning the appropriate ones.
			
			from_inst = self._load_model(join.source_cls, row[:first_cols])
			to_inst = self._load_model(join.target_cls, row[first_cols:])

			if not join.one_side:
				to_list = getattr(to_inst, attr_name, None)
				if to_list is None:
					to_list = []
					setattr(to_inst, attr_name, to_list)
				if from_inst not in to_list:
					to_list.append(from_inst)
				return to_inst
			else:
				setattr(from_inst, attr_name, to_inst)
				return from_inst
		
		result = []
		last = None
		row = self.cursor.fetchone()

		while row is not None:
			#	Load it.
			loaded = load_one(row)

			#	First time.
			if last is None:
				last = loaded

			if loaded is not last:
				#	New host.
				if one:
					#	Done, we loaded one.
					break
				
				#	Keep going.
				result.append(last)
				last = loaded

			row = self.cursor.fetchone()

		#	Eat last.
		if last is not None:
			result.append(last)

		if one:
			return result[0] if len(result) > 0 else None
		else:
			return result

	def execute(self, sql, values=tuple()):
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
				raise ex from None
		
		return self

	def save(self, *models):
		for model in models:
			model_cls = model.__class__
			self._precheck_constraints(model)
			
			self.execute(*row_creation(model))

			self._map_model(model, self.cursor.fetchone())

			model.__session__ = self

			model.__create__()
		return self

	def detach(self, model):
		del self.active_mappings[self._row_reference(model)]

		model.__session__ = None

		return self

	def delete(self, *models, cascade=False):
		for model in models:
			self.execute(*row_deletion(model, cascade))
			self.detach(model)

		return self

	def query(self, target, conditions=True, one=False, count=None, distinct=False, offset=None, order_by=tuple(), for_update=False, for_share=False):
		if conditions is False:
			return None if one else []
		
		for_ = None
		if for_share:
			for_ = 'SHARE'
		if for_update:
			for_ = 'UPDATE'
		
		if not isinstance(order_by, (list, tuple)):
			order_by = (order_by,)
		
		self.execute(*selection(target, conditions, distinct, count, offset, order_by, for_))

		#	TODO: Remove.
		def from_loader_method(loader_method):
			if one:
				row = self.cursor.fetchone()
				if row is None:
					return None

				return loader_method(target, row)
			else:
				result = []
				for i, row in enumerate(self.cursor):
					result.append(loader_method(target, row))
				return result

		if inspect.isclass(target) and issubclass(target, Model):
			return from_loader_method(self._load_model)
		elif isinstance(target, Join):
			return self._load_join(target, one)
		else:
			if isinstance(target, SQLAggregatorCall):
				one = True
			
			if one:
				return self.cursor.fetchone()[0]
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
