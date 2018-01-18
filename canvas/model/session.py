#	coding utf-8
'''
The `Session` object; ORM manager
'''

from psycopg2 import IntegrityError, connect

from ..exceptions import UnsupportedEnformentMethod, ValidationErrors
from ..utils import logger
from .columns import _sentinel
from .constraints import get_constraint
from .sql_factory import *
from .. import config

log = logger()

#	TODO: Race condition when primary key is changed between requests

def _row_reference(model):
	'''
	The canonical row reference format given
	a loaded, up-to-date model
	'''
	return f'{model.__class__.__table__}=>{model.__orm_ref__}'

class Session:

	def __init__(self):
		self.conn = connect(**config['database'])
		self.cursor = self.conn.cursor()
		#	Stores mapped rows by table name and
		#	primary key value
		self.active_mappings = {}

	def _map_model(self, model, row):
		'''
		Set model values out of a row
		:model The model object to map the row onto
		:row The row to map the model object with
		'''
		model_cls = model.__class__
		for name, column, i in model_cls.schema_iter(i=True):
			column.set_value_for(model, row[i])
		self._update_reference(model)

	def _update_reference(self, model):
		'''
		Update the reference to the row to which
		`model` is mapped
		'''
		model_cls = model.__class__

		if hasattr(model, '__orm_ref__'):
			#	Clear the existing reference
			prev_ref = _row_reference(model)
			if prev_ref in self.active_mappings:
				del self.active_mappings[prev_ref]
		
		#	Store on model and in internal mapping
		model.__orm_ref__ = model_cls.__primary_key__.value_for(model)
		self.active_mappings[_row_reference(model)] = model

	def _precheck_constraints(self, model):
		'''
		Check for constraint violations on a
		model object preceeding a commit
		'''
		#	Grab class
		model_cls = model.__class__

		#	Collect all errors
		error_dict = {}
		for name, column in model_cls.schema_iter():
			#	Read column value off model
			to_check = column.value_for(model)
			if to_check == _sentinel:
				#	Skip unset values, this is a call
				#	to `save()` and defaults aren't populated
				continue
			for constr in column.constraints:
				try:
					if not constr.check(model, to_check):
						#	Add this error and stop inspecting
						#	this column
						error_dict[name] = constr.error_message
						break
				except UnsupportedEnformentMethod: 
					#	Column didn't implement `check()`
					pass
		
		if len(error_dict) > 0:
			#	Errors occured
			raise ValidationErrors(error_dict)

	def _load_model(self, model_cls, row):
		'''
		Map a row to a model. If the row is already mapped
		by this session, update the mapping and return the
		existing object. Otherwise, create a new instance
		to map and map it.
		'''
		ref = f'{model_cls.__table__}=>{row[0]}'

		remap = ref in self.active_mappings
		if remap:
			#	This row is already mapped
			model = self.active_mappings[ref]
		else:
			#	Back-door model object creation so __init__
			#	usage is intuative
			model = model_cls.__new__(model_cls)
		
		self._map_model(model, row)
		if not remap:
			#	Dispatch load callback
			model.__on_load__()
		return model

	def execute(self, sql, values=()):
		'''
		Execute SQL with debug logging, throwing a 
		`ValidationError` when an integrity check fails.
		'''
		#	Log
		log.debug(sql)
		if len(values) > 0:
			log.debug(f'\t{str(values)}')
		
		#	Try, catching integrity errors
		try:
			self.cursor.execute(sql, values)
		except IntegrityError as e:
			#	TODO: Handle unique and other unnamed constraints
			constraint = get_constraint(e.diag.constraint_name)
			raise ValidationErrors({
				constraint.target_column.name: constraint.error_message
			})

	def save(self, model):
		'''
		Insert a table row given a model object.
		'''
		#	Grab class
		model_cls = model.__class__

		#	Precheck constraints
		self._precheck_constraints(model)

		#	Insert
		self.execute(*row_creation(model))

		#	SQL factory has the insert returning the 
		#	primary key value so we have a reference
		ref = self.cursor.fetchone()[0]

		#	Retrieve the row we just inserted so we
		#	can see populated defaults
		self.execute(*row_retrieval(model_cls, model_cls.__primary_key__ == ref))

		self._map_model(model, self.cursor.fetchone())
		#	Dispatch creation callback now that
		#	defaults are populated
		model.__on_create__()

	def delete(self, model):
		'''
		Delete the row mapped to the given model.
		'''
		#	Delete row
		self.execute(*row_deletion(model))
	
		#	Remove mapping
		del self.active_mappings[_row_reference(model)]

	def query(self, model_cls, conditions=True, one=False):
		'''
		Retrieve models from a table based on some
		conditions.
		'''
		#	Execute the select
		self.execute(*row_retrieval(model_cls, conditions))

		if one:
			#	Return the first entry
			row = self.cursor.fetchone()
			if row is None:
				return None
			return self._load_model(model_cls, row)
		else:
			#	Return all entries
			return [self._load_model(model_cls, row) for row in self.cursor]

	def commit(self):
		'''
		Write the actively mapped models into their 
		rows and commit the transaction.
		'''
		#	Update active models
		#	TODO: Check if nessesary for each
		to_commit = list(self.active_mappings.items())
		for ref, model in to_commit:
			if model.__dirty__:
				self._precheck_constraints(model)
				self.execute(*row_update(model))
				self._update_reference(model)
				#	All changes are now persistant, clear 
				#	dirty flag
				model.__dirty__ = False
		
		#	Commit transaction
		self.conn.commit()
	
	def rollback(self):
		self.conn.rollback()

	def close(self):
		self.conn.close()

	def __del__(self):
		self.close()
