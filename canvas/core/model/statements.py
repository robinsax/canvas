# coding: utf-8
'''
Top-level statement objects.
'''

from .ast import deproxy, nodeify

#	TODO: Constructor docs.

class Statement:
	'''The top-level AST node type, which must facilitate value collection.'''

	def write(self):
		'''Return an SQL, value list tuple of this statement's serialization'''
		raise NotImplementedError()

class CreateStatement(Statement):
	'''A lazy SQL `CREATE` statement.'''

	def __init__(self, target):
		self.target = deproxy(target)

	def write(self):
		return ' '.join((
			'CREATE', self.target.object_type, 'IF NOT EXISTS',
				self.target.describe()
		)), tuple()

class SelectStatement(Statement):
	'''An SQL `SELECT` statement.'''

	def __init__(self, target, condition=True, modifiers=tuple(), distinct=False):
		self.target, self.condition = deproxy(target), nodeify(condition)
		self.modifiers = modifiers
		self.distinct = distinct

	def write(self):
		values = list()
		sql = ' '.join((
			'SELECT', self.target.serialize_selection(),
			'FROM', self.target.serialize_source(values),
			'WHERE', nodeify(self.condition).serialize(values),
			*(modifier.serialize(values) for modifier in modifiers)
		))
		return sql, values

class InsertStatement(Statement):
	'''An SQL `INSERT` statement.'''

	def __init__(self, target, values):
		'''
		::target The target object reference.
		::values A list of value, object-reference-esq tuples.
		'''
		self.target = deproxy(target)
		self.values = [(nodeify(value[0]), value[1]) for value in values]

	def write(self):
		values = list()
		sql = ' '.join((
			'INSERT INTO', target.serialize(values), '(', 
				*(value[1].serialize(values) for value in self.values), 
			') VALUES (', 
				*(value[0].serialize(values) for value in self.values), 
			')'
		))
		return sql, values

class DeleteStatement(Statement):
	'''An SQL 'DELETE FROM' statement.'''

	def __init__(self, host, condition, cascade):
		self.host, self.condition = deproxy(host), condition
		self.cascade = cascade

	#	TODO: Handle cascade options.
	def write(self):
		values = list()
		sql = ' '.join((
			'DELETE FROM', self.host.serialize(values),
			'WHERE', self.condition.serialize(values)
		))
		return values, sql

class UpdateStatement(Statement):
	'''An SQL 'UPDATE' statement.'''

	def __init__(self, target, assignments, condition):
		self.target, self.condition = deproxy(target), nodeify(condition)
		self.assignments = (
			(target, nodeify(value)) for target, value in assignments
		)

	def write(self):
		values, assignment_expressions = list(), list()
		for target, value in self.assignments:
			assignment_expressions.append(
				'='.join((target.serialize(), value.serialize(values)))
			)
		sql = ' '.join((
			'UPDATE', target.serialize(),
			'SET', ', '.join(assignment_expressions),
			'WHERE', condition.serialize(values)
		))
		return sql, values
