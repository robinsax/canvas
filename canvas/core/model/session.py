# coding: utf-8
'''
The `Session` class definition.
'''

from psycopg2 import IntegrityError, connect

from ...exceptions import ValidationErrors
from ...configuration import config
from ...utils import logger
from .ast import Aggregation
from .constraints import Constraint
from .columns import Column
from .statements import InsertStatement, CreateStatement, UpdateStatement \
		DeleteStatement
from . import _sentinel

log = logger(__name__)

class Session:
	'''
	The `Session` class is used for database interaction and, transparently, 
	model management. Request context's contain a `Session` by default. 
	'''

	def __init__(self):
		'''Create a new session.'''
		self._connection = self._cursor = None
		#	A dictionary for storing all actively loaded models. Keys are
		#	of the format <host table name>=><primary key value>.
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

	def execute(self, sql, values=tuple()):
		'''
		Execute a prepared statement with constraint violation identification.
		'''
		if config.development.log_emitted_sql:
			#	Log the prepared statement.
			log.debug(sql)
			if values:
				log.debug('\t%s'%str(values))
			
		try:
			self.cursor.execute(sql, values)
		except IntegrityError as ex:
			#	Retrieve the violated constraint.
			constraint = Constraint.get(ex.diag.constraint_name)
			if not constraint:
				#	Some cases are not yet handled.
				raise NotImplementedError() from ex
			
			if isinstance(constraint, Column):
				#	The violation occured against a given column.
				raise ValidationErrors({
					constraint.host.name: constraint.error_message
				})
			else:
				#	Table-level violation.
				raise ValidationErrors(constraint.errors_message)
		
		#	Chain.
		return self

	def execute_statement(statement):
		'''Execute a `Statement` object.'''
		sql, values = statement.write()
		self.execute(sql + ';', values)

	def save(self, *models):
		'''Save `models` to the database.'''
		for model in models:
			table = model.__class__.__table__

			#	Precheck for violations.
			self.precheck_constraints(model)

			#	Collect values, ignoring sentinels which may be in-database
			#	defaults.
			to_insert = list()
			for column in table.columns:
				value = getattr(model, column.name)
				if value is not _sentinel:
					values.append((value, column))
			
			#	Create and execute an insert statement.
			self.execute_statement(InsertStatement(model.__class__, values))
			#	Re-load the result onto the model.
			self.assign_row_to_model(model, self.cursor.fetchone())
		return self

	def detach(self, model):
		'''Detach an object from its mapped row.'''
		table = model.__class__.__table__
		#	Delete the entry.
		del self.loaded_models[
			'=>'.join([table.name, table.primary_key.value_on(model)])
		]
		#	Inform the model.
		model.__loaded__(None)

		return self

	def delete(self, *models, cascade=False):
		'''Delete each of `models` from the database.'''
		for model in models:
			table = model.__class__.__table__
			#	Create and execute a delete statement.
			condition = table.primary_key == table.primary_key.value_on(model)
			self.execute_statement(*DeleteStatement(table, condition, cascade))
			#	Detach the now-orphaned model.
			self.detach(model)

		return self

	def query(self, target, condition=True, one=False, count=None, 
				offset=None, distinct=False, order=tuple(), for_update=False, 
				for_share=False):
		'''
		Query the database, returning loaded models.
		::condition A flag-like AST node representing the query condition.
		::one Whether to retrieve a single entry or a list.
		::count The number of entries to retrieve.
		::offest The offset at which to begin.
		::distinct Whether to only retrieve distinct entries.
		::order One or more ordering directive generated by the `Column.asc` or 
			`Column.desc` methods.
		::for_update Whether all selections should be `FOR UPDATE`.
		::for_share Whether all selections should be `FOR SHARE`.
		'''
		if condition is False:
			#	Nothing would be returned.
			return None if one else list()
		#	Process arguments.
		if isinstance(target, Aggregation):
			one = True
		
		#	Create a list of modifier AST nodes.
		modifiers = list()

		#	Transform optional arguments to modifiers.
		if count:
			modifiers.append(Literal('COUNT', count))
		if offset:
			modifiers.append(Literal('OFFSET', offset))
		if not isinstance(order, (list, tuple)):
			order = (order,)
		modifiers.append(Literal('ORDER BY', Literal(*order, joiner=', ')))
		if for_share or for_update:
			which = 'SHARE' if for_share else 'UPDATE'
			modifiers.append(Literal('FOR', which))
		
		self.execute_statement(
			SelectStatement(target, condition, modifiers, distinct)
		)

		#	Retrieve a loader and return.
		loader = target.get_loader()
		if one:
			return loader.load_next(self.cursor.fetchone(), self)
		else:
			return [
				loader.load_next(row) for row in self.cursor.fetchall()
			]

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
