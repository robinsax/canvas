#	coding utf-8
'''
Column-value constraint representations.
'''

import re

from urllib.parse import quote

from ...exceptions import (
	InvalidConstraint,
	ValidationErrors
)
from ...namespace import export, export_ext

_constraint_map = dict()

@export
def get_constraint(name):
	return _constraint_map.get(name, None)

@export_ext
class Constraint:

	def __init__(self, name_postfix, error_message):
		self.name_postfix, self.error_message = name_postfix, error_message

		self.column, self.name = (None,)*2

	def resolve(self, column):
		self.column = column
		self.name = '%s_%s_%s'%(column.model.__table__, column.name, self.name_postfix)

		_constraint_map[self.name] = self
	
	def as_client_parsable(self):
		raise NotImplementedError()

	def as_sql(self):
		raise NotImplementedError()

	def check(self, model_obj, value):
		raise NotImplementedError()

	def check_with_throw(self, model, value):
		if not self.check(model, value):
			raise ValidationErrors({
				self.column.name: self.error_message
			})

@export
class RegexConstraint(Constraint):

	def __init__(self, error_message, regex, ignore_case=False, negative=False):
		super().__init__('format', error_message)
		self.regex = regex
		self.ignore_case, self.negative = ignore_case, negative

	def as_client_parsable(self):
		as_flag = lambda b: '1' if b else '0'

		return 'regex:%s:%s:%s'(
			quote(self.regex), 
			as_flag(self.ignore_case), 
			as_flag(self.negative)
		)
	
	def as_sql(self):
		operator = '~'
		if self.negative:
			operator = '!%s'%operator
		if self.ignore_case:
			operator = '%s*'%operator
		return 'CHECK (%s %s \'%s\')'%(
			self.column.serialize([]),
			operator,
			self.regex
		)

	def check(self, model, value):
		flags = re.I if self.ignore_case else 0

		return re.match(self.regex, value, flags=flags) is not None

@export
class RangeConstraint(Constraint):

	def __init__(self, error_message, max_value=None, min_value=None):
		super().__init__('range', error_message)
		
		if max_value is None and min_value is None:
			raise InvalidConstraint('Invalid range: none specified')
		if (max_value is not None and min_value is not None 
				and max_value <= min_value):
			raise InvalidConstraint('Invalid range: empty')

		self.max_value, self.min_value = max_value, min_value

	def as_client_parsable(self):
		return 'range:%s,%s'%(
			'null' if self.max_value is None else self.max_value,
			'null' if self.min_value is None else self.min_value
		)

	def as_sql(self):
		column_reference = self.column.serialize([])
		
		ends = []
		if self.max_value is not None:
			ends.append('%s <= %s'%(
				column_reference, 
				self.max_value
			))
		if self.min_value is not None:
			ends.append('%s <= %s'%(
				column_reference, 
				self.min_value
			))
		ends = ' AND '.join(ends)

		return 'CHECK (%s)'%ends

@export
class UniquenessConstraint(Constraint):

	def __init__(self, error_message='Must be unique'):
		super().__init__('uniqueness', error_message)

	def as_sql(self):
		return 'UNIQUE'

@export
class NotNullConstraint(Constraint):

	def __init__(self, error_message='Required'):
		super().__init__('existance', error_message)

	def as_sql(self):
		return 'CHECK (%s IS NOT NULL)'%self.column.name

	def check(self, model, value):
		return value is not None
