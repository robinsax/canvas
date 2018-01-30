#	coding utf-8
'''
The `Session` object definition.
'''

from psycopg2 import (
	IntegrityError, 
	connect
)

from ..exceptions import (
	UnsupportedEnformentMethod, 
	ValidationErrors
)
from ..utils import logger
from .columns import _sentinel
from .constraints import get_constraint
from .sql_factory import *
from .. import config

log = logger()

#	TODO: Resolve race condition when primary key 
#	is changed between requests.

class Session:
	'''
	The `Session` object maintains a consecutive set 
	of database transactions.
	'''

	def __init__(self):
		#	Eagerly create a connection and cursor
		#	since psycopg2 is lazy in actualizing them.
		self.conn = connect(**config['database'])
		self.cursor = self.conn.cursor()
		
		#	Stores the active row reference to model
		#	instance mapping.
		self.active_mappings = {}

	def _row_reference(self, model):
		'''
		The canonical row reference format for the 
		row reference to model instance mapping.
		'''
		return f'{model.__class__.__table__}=>{model.__orm_ref__}'

	def _map_model(self, model, row):
		'''
		Set values on a model object from a row in the 
		corresponding table.

		:model The model object to populate with the row 
			values.
		:row The row values.
		'''
		#	Set the row values onto the object.
		for name, column, i in model.__class__.schema_iter(i=True):
			column.set_value_for(model, row[i])
		
		#	Update the stored row reference for the
		#	newly mapped model instance.
		self._update_reference(model)

	def _update_reference(self, model):
		'''
		Update the stored reference to the row mapped to
		`model`.
		'''

		#	Ensure an existing reference doesn't exist.
		if hasattr(model, '__orm_ref__'):
			#	Clear the existing reference.
			prev_ref = self._row_reference(model)
			if prev_ref in self.active_mappings:
				del self.active_mappings[prev_ref]
		
		#	Store referenced primary key value on model and 
		#	in internal mapping.
		model.__orm_ref__ = model.__class__.__primary_key__.value_for(model)
		self.active_mappings[self._row_reference(model)] = model

	def _precheck_constraints(self, model):
		'''
		Check for cumulative constraint violations on a 
		model object preceeding a commit, raising a
		`ValidationErrors` if any exist and doing nothing
		otherwise.
		'''
		#	Check each constraint and collect those violated in
		#	a constraint name to error message mapping.
		error_dict = {}
		for name, column in model.__class__.schema_iter():
			#	Read column value for this model.
			to_check = column.value_for(model)
			if to_check == _sentinel:
				#	Skip unset values, this is a call
				#	to `save()` and defaults aren't populated.
				continue
			for constr in column.constraints:
				try:
					if not constr.check(model, to_check):
						#	Add this error and stop inspecting
						#	this column.
						error_dict[name] = constr.error_message
						break
				except UnsupportedEnformentMethod: 
					#	Column didn't implement the `check()` 
					#	method.
					pass
		
		if len(error_dict) > 0:
			#	Raise the errors.
			raise ValidationErrors(error_dict)

	def _load_model(self, model_cls, row):
		'''
		Map a row to a model. If the row is already mapped
		by this session, update the mapping and return the
		existing object. Otherwise, create a new instance
		and map it.
		'''
		#	Create the row reference. An invariant within
		#	all database reads and write is that primary
		#	keys are referenced first in SQL.
		ref = f'{model_cls.__table__}=>{row[0]}'
		
		remap = ref in self.active_mappings
		if remap:
			#	This row is already mapped.
			model = self.active_mappings[ref]
		else:
			#	Create the model object manually so `__init__`
			#	usage is intuative.
			model = model_cls.__new__(model_cls)
		
		#	Map the row onto the model instance.
		self._map_model(model, row)
		if not remap:
			#	Dispatch load callback.
			model.__on_load__()

		return model

	def execute(self, sql, values=()):
		'''
		Execute SQL with debug logging, throwing a `ValidationError` 
		when an integrity check fails.
		'''
		#	Log the emitted SQL format at the debug level.
		log.debug(sql)
		if len(values) > 0:
			#	Log the values too.
			log.debug(f'\t{str(values)}')
		
		#	Try to execute and catch integrity errors.
		try:
			self.cursor.execute(sql, values)
		except IntegrityError as e:
			#	Get the constraint object given the violated name.
			constraint = get_constraint(e.diag.constraint_name)
			#	Raise a validation error containing the constraint info.
			raise ValidationErrors({
				constraint.target_column.name: constraint.error_message
			})
		
		return self

	def save(self, model):
		'''
		Insert a new table row given a constructed model object.
		'''
		model_cls = model.__class__

		#	Check constraints before insertion so a cumulative
		#	exception can be raised if multiple constraints
		#	are violated.
		self._precheck_constraints(model)

		#	Perform the insertion.
		self.execute(*row_creation(model))

		#	SQL factory has the insert returning the primary key 
		#	value so we have a reference in the case of in-SQL column
		#	defaults.
		ref = self.cursor.fetchone()[0]

		#	Retrieve the row we just inserted so we can see populated 
		#	defaults.
		self.execute(*row_retrieval(model_cls, model_cls.__primary_key__ == ref))

		#	Populate the model object with the retrieved row.
		self._map_model(model, self.cursor.fetchone())

		#	Dispatch creation callback.
		model.__on_create__()
		return self

	def delete(self, model):
		'''
		Delete the row mapped to a loaded model.
		'''
		#	Perform the deletion.
		self.execute(*row_deletion(model))

		#	Remove the mapping.
		del self.active_mappings[self._row_reference(model)]
		return self

	#	TODO: Redoc.
	def query(self, target, conditions=True, one=False, order_by=None, descending=False):
		'''
		Retrieve rows from a table based on some query, then
		load them as models and return the resulting model
		list.

		:target The model class (must have been decorated
			with `model.schema()`).
		:conditions A primitive type or comparison on class-level
			column attributes.
		:one Whether to return the first result only, or `None`
			if there are not results.
		'''
		#	Handle a contradiction as the condition.
		if conditions is False:
			return None if one else []
		
		#	Check if order specified.
		order = (order_by, not descending) if order_by is not None else None
		
		#	Execute the selection.
		if hasattr(target, '__schema__'):
			#	Return model objects.
			self.execute(*row_retrieval(target, conditions, order))

			if one:
				#	Return the first entry or `None`.
				row = self.cursor.fetchone()
				if row is None:
					return None

				return self._load_model(target, row)
			else:
				#	Return a list containing all entries.
				return [self._load_model(target, row) for row in self.cursor]
		elif isinstance(target, SQLExpression):
			#	Return a scalar.
			#	TODO: Improve the condition + finish.
			raise NotImplemented()
			self.execute(*column_retrieval(target, conditions, order))
		else:
			raise InvalidQuery('Bad query target')

	def commit(self):
		'''
		Write all actively mapped model instances into their 
		rows and commit the transaction.
		'''
		#	Emit row update SQL for each modified model 
		#	instance
		to_commit = list(self.active_mappings.items())
		for ref, model in to_commit:
			if model.__dirty__:
				#	This model instance has been modified.

				#	Throw a `ValidationErrors` for each column
				#	in which constraints are violated.
				self._precheck_constraints(model)

				#	Execute the update.
				self.execute(*row_update(model))

				#	Update the internal reference in case the
				#	primary key changed.
				self._update_reference(model)

				#	All changes are now persistant, clear 
				#	the dirty flag.
				model.__dirty__ = False
		
		#	Commit the transaction.
		self.conn.commit()
		return self

	def reset(self):
		'''
		Rollback this session, then remove all active mappings.
		'''
		#	Rollback.
		self.rollback()
		#	Reset active mappings.
		self.active_mappings = {}
		return self
	
	def rollback(self):
		'''
		Undo all changes made during the current transaction.
		
		TODO: Rollback changes to model instances too.
		'''
		self.conn.rollback()
		return self

	def close(self):
		'''
		Close the underlying database connection for this
		session.
		'''
		self.conn.close()
		return self

	def __del__(self):
		'''
		A deconstructor to ensure no database connections
		are orphaned.
		'''
		self.close()
