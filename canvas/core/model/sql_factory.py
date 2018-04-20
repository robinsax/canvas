#	coding utf-8
'''
SQL serialization.
'''

import inspect

from ...exceptions import (
	InvalidQuery,
	UnadaptedType
)
from .sql_nodes import (
	SQLExpression,
	SQLComparison,
	SQLAggregatorCall
)
from .columns import Column
from .model import Model
from .joins import Join
from .columns import _sentinel

def table_creation(model_cls):

	def column_definition(column):
		if column.is_fk:
			target = column.reference
			column_sql = ' '.join([
				column.name, target.sql_type,
				'REFERENCES',
				target.model.__table__, '(', target.name, ')'
			])
		else:
			column_sql = ' '.join([column.name, column.sql_type])
			if column.primary_key:
				column_sql += ' PRIMARY KEY'

		for constraint in column.constraints:
			try:
				sql_repr = constraint.as_sql()
			except NotImplementedError: 
				continue
			
			column_sql = ' '.join([
				column_sql,
				'CONSTRAINT', constraint.name, sql_repr
			])
		
		return column_sql

	statement = ' '.join([
		'CREATE TABLE IF NOT EXISTS',
		model_cls.__table__, '(', 
			', '.join([
				column_definition(column) for column in model_cls.__schema__.values()
			]),
		');'
	])
	return statement, ()

def selection(target, query, ordering, for_):
	values = []
	
	if query is True:
		condition = None
	elif isinstance(query, SQLExpression):
		condition = query.as_condition(values)
	else:
		raise InvalidQuery('Bad query condition: %s'%repr(query))

	if inspect.isclass(target) and issubclass(target, Model):
		selection = ', '.join(target.__schema__.keys())
		source = target.__table__
	elif isinstance(target, Join):
		selection = target.serialize_selection()
		source = target.serialize_source()
	elif isinstance(target, SQLExpression):
		selection = target.serialize([])

		if isinstance(target, SQLAggregatorCall):
			target = target.column
		source = target.model.__table__
	else:
		raise InvalidQuery('Bad query selection: %s'%repr(target))

	statement = ' '.join([
		'SELECT', selection,
		'FROM', source
	])

	if condition is not None:
		statement = ' '.join([
			statement,
			condition
		])
	if ordering is not None:
		column, ascending = ordering
		statement = ' '.join([
			statement,
			'ORDER BY', column.serialize(), 'ASC' if ascending else 'DESC'
		])
	if for_ is not None:
		statement = ' '.join((
			statement,
			'FOR %s'%for_
		))

	statement += ';'
	return statement, values

def row_update(model):
	model_cls = model.__class__
	values = []

	assignments = []
	for column_name in model.__dirty__:
		value = model_cls.__schema__[column_name].value_for(model)
		
		if value is _sentinel:
			#	This is a call to save() and this column has not been 
			#	populated; allow it to default in Postgres.
			continue
		
		values.append(value)
		assignments.append('%s = %%s'%column_name)

	row_access = '%s = %%s'%model_cls.__primary_key__.name
	values.append(model.__mapped_as__)
	
	statement = ' '.join([
		'UPDATE', model_cls.__table__,
		'SET', ', '.join(assignments),
		'WHERE', row_access, ';'
	])
	return statement, values

def row_creation(model):
	model_cls = model.__class__
	values = []

	order = []
	for name, column in model_cls.__schema__.items():
		value = column.value_for(model)

		if value is _sentinel:
			#	This is a call to save() and this column has not been 
			#	populated; allow it to default in Postgres.
			continue

		order.append(name)
		values.append(value)
	
	insertions = 'DEFAULT VALUES'
	if len(order) > 0:
		insertions = ' '.join(['(', 
			', '.join(order),
		') VALUES (',
			', '.join(['%s' for x in order]),
		')'])

	statement = ' '.join([
		'INSERT INTO', model_cls.__table__, insertions, 'RETURNING ', ', '.join(model_cls.__schema__.keys()), ';'
	])
	return statement, values

def row_deletion(model):
	model_cls = model.__class__
	primary_key = model_cls.__primary_key__.name

	#	Return formatted statement.
	statement = ' '.join([
		'DELETE FROM', model_cls.__table__,
		'WHERE', primary_key, '= %s;'
	])
	values = (model.__mapped_as__,)
	return statement, values
