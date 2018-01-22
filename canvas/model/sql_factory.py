#	coding utf-8
'''
SQL serialization.
'''

from ..exceptions import UnsupportedEnformentMethod
from .columns import (
	Column, 
	ForeignKeyColumnType,
	_ColumnComparator, 
	_sentinel
)

#	These exports are intended for in-package
#	use only.
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
	Serialize the pre-determined column order for the 
	given model class.
	'''
	return ', '.join(model_cls.__columns__)

def comparator_expression(expr, _values=None):
	'''
	Recursively resolve a n-column comparsion tree
	and generate the corresponding value list via
	inorder traversal.
	'''
	#	_values is an array passed through recursion
	#	to collect the ordered values for the
	#	prepared statement. If it isn't set, this
	#	is the expression-level call.
	top = _values is None
	if top:
		#	Initialize for recursion.
		_values = []
	
	#	Parse this tree node.
	if isinstance(expr, _ColumnComparator):
		#	This node is a comparision; recurse on 
		#	each child.
		l_result = comparator_expression(expr.left, _values)
		r_result = comparator_expression(expr.right, _values)
		
		#	Handle the NULL case of SQL operator
		#	representation.
		if r_result == 'NULL':
			if expr.operator == '=':
				expr.operator = 'IS'
			if expr.operator == '<>':
				expr.operator = 'IS NOT'
		
		#	Create comparison SQL.
		ret = f'{l_result} {expr.operator} {r_result}'

		#	Apply precedence and inversion modifiers.
		if expr.grouped:
			ret = f'({ret})'
		if expr.inverted:
			ret = f'NOT {ret}'
	elif isinstance(expr, Column):
		#	This node is a column reference.
		ret = f'{expr.model.__table__}.{expr.name}'
	elif expr is None:
		#	This node is a NULL value.
		ret = 'NULL'
	elif isinstance(expr, bool):
		#	This node is a boolean.
		ret = 'TRUE' if expr else 'FALSE'
	elif isinstance(expr, (int, float, str)):
		#	This node is a prepared value, serialize
		#	it as a format and append value to _values list
		_values.append(expr)
		ret = '%s'

	if top:
		#	Return the SQL-serialization and value list
		#	for the statement.
		return ret, _values

	#	A recursive call invoked this function, return
	#	only the SQL since `_values` is shared.
	return ret

def enum_creation(enum_cls):
	'''
	In-Postgres enumerable type creation. Complicated by the 
	lack of an IF NOT EXISTS option.
	'''
	#	Get the in-Postgres type name.
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
	Serialize a table creation with IF NOT EXISTS option since 
	table creation is issued every time canvas is initialized.
	'''

	def column_definition(col):
		'''
		Serialize a column generation.
		'''
		#	Create definition base; name and type.
		col_sql = f'{col.name} {col.type.sql_type}'

		if col.primary_key:
			#	Add primary key modifier.
			col_sql = f'{col_sql} PRIMARY KEY'

		#	Add foreign key target if applicable.
		if isinstance(col.type, ForeignKeyColumnType):
			target = col.type.target_model
			col_sql = f'{col_sql} REFERENCES {target.__table__} ({target.name})'
		
		#	Add all constraints that support SQL serialization.
		for constr in col.constraints:
			try:
				col_sql = f'{col_sql} CONSTRAINT {constr.name} {constr.as_sql()}'
			except UnsupportedEnformentMethod:
				#	This constraint isn't representable in SQL.
				pass
		
		return col_sql

	#	Define each column and join
	col_defns = ', '.join([
		column_definition(o) for n, o in model_cls.schema_iter()
	])
	
	#	Return formatted statement.
	return f'CREATE TABLE IF NOT EXISTS {model_cls.__table__} ({col_defns});', ()

def row_retrieval(model_cls, query):
	'''
	Serialize a row retrieval based on some query expression.

	:model_cls The targeted model class.
	:query The query. Either a primitive value or a 
		model-class-level column comparison.
	'''
	#	Serialize the query.
	expr, vals = comparator_expression(query)

	#	Return formatted statement.
	return f'SELECT {_column_ordering(model_cls)} FROM {model_cls.__table__} WHERE {expr};', vals

def row_update(model):
	'''
	Serialize a row update based on a loaded model object.

	:model The model instance whose row to update.
	'''
	model_cls = model.__class__

	#	Create assignment statement.
	assignments, values = [], []
	for name, column in model_cls.schema_iter():
		#	Retrieve the column value.
		value = column.value_for(model)

		if value is _sentinel:
			#	This is a call to `save()` and this column
			#	has not been populated; allow it to default.
			continue
		values.append(value)
		assignments.append(f'{name} = %s')
	
	#	Comma-seperate assignments.
	assignments = ', '.join(assignments)
	
	#	Create row access expression.
	row_access = f'{model_cls.__primary_key__.name} = %s'
	values.append(model.__orm_ref__)
	
	#	Return formatted statement.
	return f'UPDATE {model_cls.__table__} SET {assignments} WHERE {row_access};', values

def row_creation(model):
	'''
	Serialize a row insertion based on a constructed 
	model object.
	'''
	model_cls = model.__class__

	#	We can't rely on `__columns__` for order here since 
	#	sentineled values are not inserted.
	values, order = [], []
	for name, column in model_cls.schema_iter():
		if column.value_for(model) == _sentinel:
			#	Skip this column to allow defaults to
			#	take effect.
			continue
		order.append(name)
		values.append(column.value_for(model))
	
	#	Comma seperate assignments and order.
	assignments = ', '.join(['%s' for x in order])
	order = ', '.join(order)

	#	Caller is going to read primary key from cursor
	#	to obtain a row reference in the case of SERIAL
	#	and other in-SQL defaulted primary key values.
	pk_col = model_cls.__primary_key__.name

	#	Return formatted statement.
	return f'INSERT INTO {model_cls.__table__} ({order}) VALUES ({assignments}) RETURNING {pk_col};', values

def row_deletion(model):
	'''
	Delete the corresponding row for the given
	model object
	'''
	model_cls = model.__class__

	#	Create row access expression.
	pk_col = model_cls.__primary_key__.name

	#	Return formatted statement.
	return f'DELETE FROM {model_cls.__table__} WHERE {pk_col} = %s;', (model.__orm_ref__,)
