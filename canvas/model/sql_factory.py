#	coding utf-8
'''
All SQL generation aside from that of
constriants
'''

from ..exceptions import UnsupportedEnformentMethod
from .columns import (
	Column, 
	ColumnComparator, 
	ForeignKeyColumnType,
	_sentinel
)

__all__ = [
	'table_creation',
	'comparator_expression',
	'row_retrieval',
	'row_creation',
	'row_update',
	'row_deletion'
]

def _column_ordering(model_cls):
	'''
	Column retrieval order is decided
	arbitrarily by `schema()`; serialize
	that order as SQL
	'''
	return ', '.join(model_cls.__columns__)

def comparator_expression(expr, _values=None):
	'''
	Recursively resolve expressions stored in
	`ColumnComparator`s and generate an equivalent
	prepared SQL expression and value list via
	inorder traversal.
	'''
	#	_values is an array passed through recursion
	#	to collect the ordered values for the
	#	prepared statement. If it isn't set, this
	#	is the initial call/top of the expression
	top = _values is None
	if top:
		#	Initialize to be passed down
		_values = []
	
	#	Parse this expression node
	if isinstance(expr, ColumnComparator):
		#	Node resolves as comparision;
		#	recurse on each child
		l_res = comparator_expression(expr.left, _values)
		r_res = comparator_expression(expr.right, _values)
		
		#	Handle the NULL case for SQL operator
		#	representation
		if r_res == 'NULL':
			if expr.operator == '=':
				expr.operator = 'IS'
			if expr.operator == '<>':
				expr.operator = 'IS NOT'
		
		#	Create comparison SQL
		ret = f'{l_res} {expr.operator} {r_res}'

		#	Apply precedence and inversion
		#	modifiers
		if expr.grouped:
			ret = f'({ret})'
		if expr.inverted:
			ret = f'NOT {ret}'
	elif isinstance(expr, Column):
		#	Node resolves as table reference
		ret = f'{expr.model.__table__}.{expr.name}'
	elif expr is None:
		#	Node resolves as NULL value
		ret = 'NULL'
	elif isinstance(expr, bool):
		#	Node resolves as boolean
		ret = 'TRUE' if expr else 'FALSE'
	elif isinstance(expr, (int, float, str)):
		#	Node resolves as prepared value,
		#	append value to _values list
		_values.append(expr)
		ret = '%s'

	#	Caller is expecting statement and values
	if top:
		return ret, _values
	#	Recursive calls expecting SQL only as
	#	_values is shared
	return ret

def enum_creation(enum_cls):
	'''
	Enum type creation. Complicated by the lack of
	an IF NOT EXISTS option.
	'''
	name = enum_cls.__type_name__
	type_format = ', '.join(['%s']*len(enum_cls))
	return f'''
		DO $$ BEGIN
			IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = {name}) THEN
				CREATE TYPE {name} AS ENUM ({type_format});
			END IF;
		END$$;
	''', [e.name for e in enum_cls]

def table_creation(model_cls):
	'''
	Table creation SQL with IF NOT EXISTS option
	since table creation is issued on every boot.
	'''

	#	Defines a single column for creation
	def column_definition(col):
		#	Create definition base; name and type
		col_sql = f'{col.name} {col.type.sql_type}'

		#	Add primary key
		if col.primary_key:
			col_sql = f'{col_sql} PRIMARY KEY'

		#	Add foreign key target if applicable
		if isinstance(col.type, ForeignKeyColumnType):
			target = col.type.target_model
			col_sql = f'{col_sql} REFERENCES {target.__table__} ({target.name})'
		
		#	Add all constraints that support SQL serialization
		for constr in col.constraints:
			try:
				col_sql = f'{col_sql} CONSTRAINT {constr.name} {constr.as_sql()}'
			except UnsupportedEnformentMethod: pass
		return col_sql

	#	Define each column, joining with comma
	col_defns = ', '.join([
		column_definition(o) for n, o in model_cls.schema_iter()
	])
	
	#	Form statement
	return f'CREATE TABLE IF NOT EXISTS {model_cls.__table__} ({col_defns});', ()

def row_retrieval(model_cls, query):
	'''
	Retrieve rows based on some query expression
	'''
	#	Parse the query
	expr, vals = comparator_expression(query)

	#	Form statement
	return f'SELECT {_column_ordering(model_cls)} FROM {model_cls.__table__} WHERE {expr};', vals

def row_update(model):
	'''
	Update a row based on a loaded model object
	'''
	#	Grab class
	model_cls = model.__class__

	#	Create assignment statement
	assignments, values = [], []
	for name, column in model_cls.schema_iter():
		value = column.serialized_for(model)
		if value is _sentinel:
			continue
		values.append(value)
		assignments.append(f'{name} = %s')
	
	#	Comma-seperate assignments
	assignments = ', '.join(assignments)
	
	#	Create row access expression
	row_access = f'{model_cls.__primary_key__.name} = %s'
	values.append(model.__orm_ref__)
	
	#	Form statement
	return f'UPDATE {model_cls.__table__} SET {assignments} WHERE {row_access};', values

def row_creation(model):
	'''
	Create a row based on a new model object
	'''
	#	Grab class
	model_cls = model.__class__

	#	We can't rely on __columns__ for order here 
	#	since sentinel values will not be inserted 
	#	(to allow in-SQL default to take effect)
	values, order = [], []
	for name, column in model_cls.schema_iter():
		if column.value_for(model) == _sentinel:
			continue
		order.append(name)
		values.append(column.serialized_for(model))
	
	#	Comma seperate assignments and order
	assignments = ', '.join(['%s' for x in order])
	order = ', '.join(order)

	#	Caller is going to read primary key from cursor
	#	to obtain a row reference in the case of SERIAL
	#	and other in-SQL defaulted values
	pk_col = model_cls.__primary_key__.name

	#	Form statement
	return f'INSERT INTO {model_cls.__table__} ({order}) VALUES ({assignments}) RETURNING {pk_col};', values

def row_deletion(model):
	'''
	Delete the corresponding row for the given
	model object
	'''
	#	Grab class
	model_cls = model.__class__

	#	Create row access expression
	pk_col = model_cls.__primary_key__.name

	#	Form statement
	return f'DELETE FROM {model_cls.__table__} WHERE {pk_col} = %s;', (model.__orm_ref__,)
