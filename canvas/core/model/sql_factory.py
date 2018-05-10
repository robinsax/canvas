#	coding utf-8
'''
SQL serialization.
'''

import inspect

from ...exceptions import (
	InvalidQuery,
	UnadaptedType
)
from ...configuration import config
from .sql_nodes import (
	SQLExpression,
	SQLComparison,
	SQLAggregatorCall
)
from .columns import Column
from .model import Model
from .columns import _sentinel, OrderedColumnReference
from .joins import Join

#	TODO: More transactionality.

def table_creation(model_cls):

	def column_definition(column):
		if column.is_fk:
			target = column.reference
			column_sql = ' '.join((
				column.name, target.sql_type,
				'REFERENCES',
				target.model.__table__, '(', target.name, ')'
			))
			
			if config.database.eager_drop_cascades:
				column_sql = ' '.join((column_sql, 'ON DELETE CASCADE'))
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

def selection(target, query, distinct, count, offset, ordering, for_):
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
		'SELECT', 'DISTINCT' if distinct else '', selection,
		'FROM', source
	])

	if condition is not None:
		statement = ' '.join([
			statement,
			condition
		])
	if len(ordering) > 0:
		parts = [statement, 'ORDER BY']
		first = True
		for one in ordering:
			ascending = True
			if isinstance(one, OrderedColumnReference):
				column = one.column
				ascending = one.ascending
			else:
				column = one
			
			if not first:
				parts.append(',')
			first = False
			
			parts.extend((column.serialize(), 'ASC' if ascending else 'DESC'))
			
		statement = ' '.join(parts)
	if count is not None:
		statement = ' '.join([
			statement, 'LIMIT', str(count)	
		])
	if offset is not None:
		statement = ' '.join([
			statement, 'OFFSET', str(offset)
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

def row_deletion(model, cascade):
	model_cls = model.__class__
	primary_key = model_cls.__primary_key__.name

	statement = ' '.join((
		'DELETE FROM', model_cls.__table__,
		'WHERE', primary_key, '= %s;'
	))

	if cascade and not config.database.eager_drop_cascades:
		#	Remove foreign keys, replacing them with cascades, then 
		#	reapply them. Bad for performance, good for safety.
		fk_cols = [c for c in model_cls.__schema__.values() if c.is_fk]

		for my_column in model_cls.__schema__.values():
			for column in my_column.incoming_fks:
				table_name = column.model.__table__

				constraint_name = '%s_%s_fkey'%(table_name, column.name)
				constraint_base_sql = ' '.join((
					'CONSTRAINT', constraint_name, 
					'FOREIGN KEY (', column.name, ') REFERENCES',
					model_cls.__table__, '(', my_column.name, ')'
				))

				statement = ' '.join((
					'ALTER TABLE', table_name,
						'DROP CONSTRAINT', constraint_name,
					';',
					'ALTER TABLE', table_name,
						'ADD', constraint_base_sql,
						'ON DELETE CASCADE',
					';',
					statement,
					'ALTER TABLE', table_name,
						'DROP CONSTRAINT', constraint_name,
					';',
					'ALTER TABLE', table_name,
						'ADD', constraint_base_sql,
					';'
				))

		statement = ' '.join(('BEGIN;', statement, 'COMMIT;'))

	values = (model.__mapped_as__,)
	return statement, values
