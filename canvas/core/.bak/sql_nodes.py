#	coding utf-8
'''
SQL statement node definitions.
'''

from ...exceptions import UnadaptedType
from .type_adapters import _adapted_types

class SQLExpression:
	
	def serialize_node(self, node, values):
		if isinstance(node, SQLExpression):
			return node.serialize(values)
		elif node is None:
			return 'NULL'
		elif isinstance(node, bool):
			return 'TRUE' if node else 'FALSE'
		elif isinstance(node, tuple(_adapted_types)):
			values.append(node)
			return '%s'
		else:
			raise UnadaptedType(repr(node))

	def as_condition(self, values):
		return 'WHERE %s'%self.serialize(values)

	def serialize(self, values):
		raise NotImplementedError()

class SQLComparison(SQLExpression):

	def __init__(self, left, right, operator):
		self.left, self.right = (left, right)
		self.operator = operator
		
		self.inverted = False
		self.grouped = False

	def serialize(self, values):
		left_sql = self.serialize_node(self.left, values)
		right_sql = self.serialize_node(self.right, values)

		if right_sql == 'NULL':
			if self.operator == '=':
				self.operator = 'IS'
			if self.operator == '<>':
				self.operator = 'IS NOT'

		sql = ' '.join([left_sql, self.operator, right_sql])

		if self.grouped:
			sql = '(%s)'%sql
		if self.inverted:
			sql = 'NOT %s'%sql
		return sql

	def group(self):
		self.grouped = True
		return self
	
	def __invert__(self):
		self.grouped = True
		self.inverted = True
		return self

	def __and__(self, other):
		return SQLComparison(self, other, 'AND')

	def __rand__(self, other):
		return SQLComparison(other, self, 'AND')

	def __or__(self, other):
		return SQLComparison(self, other, 'OR')

	def __ror__(other, self):
		return SQLComparison(self, other, 'OR')

class SQLAggregatorCall(SQLExpression):

	def __init__(self, func, column, weight=0):
		from .columns import Column

		if not isinstance(column, Column):
			raise InvalidQuery('Aggregator parameter is not a column')

		self.func, self.column = func, column

		#	Weight is used for the `max()` and `min()` trick.
		self.weight = weight

	def as_condition(self, values):
		return ' '.join([
			'WHERE', self.column.name,
			'= (SELECT', self.serialize(values), 'FROM', self.column.model.__table__, ')'
		])
		
	def serialize(self, values):
		return '%s(%s)'%(self.func, self.serialize_node(self.column, values))

	def __gt__(self, other):
		return self.weight > other.weight
