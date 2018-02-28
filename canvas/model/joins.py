#	coding utf-8
'''
Join generation functions.
'''

from .sql_factory import SQLExpression

class SQLJoin(SQLExpression):

	def __init__(self, l_model, r_model, typ):
		self.typ = typ
		self.l_model, self.r_model = l_model, r_model

	def serialize(self, values):
		return f'{self.typ} ()'

def join(left, right):
	return SQLJoin('LEFT OUTER JOIN', left, right)
