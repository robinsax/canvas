#	coding utf-8
'''
Constraints on data
'''

import re

from urllib.parse import quote

from ..exceptions import (
	ColumnDefinitionError, 
	UnsupportedEnformentMethod
)

__all__ = [
	'get_constraint',
	'Constraint',
	'RegexConstraint',
	'RangeConstraint',
	'UniquenessConstraint',
	'NotNullConstraint'
]

_constraint_map = {}

def get_constraint(name):
	'''
	Return the `Constraint` with name `name`, 
	or `None` if there isn't one.
	'''
	return _constraint_map.get(name, None)

class Constraint:
	'''
	Base constraint class, enforcing a name,
	target column, error message, and two methods.
	'''

	def __init__(self, name, error_message):
		'''
		:name The internal name of this constraint
		:error_message The user-facing error message to 
			display when this constraint is violated
		'''
		self.name = name
		self.error_message = error_message
		self.target_column = None	# Placeholder

		_constraint_map[name] = self
	
	def as_client_parsable(self):
		'''
		Constraints that implement this method can be sent
		to the client for live input validation.
		'''
		raise UnsupportedEnformentMethod()

	def as_sql(self):
		'''
		Constraints that implement this method can be embedded
		in table definitions.
		'''
		raise UnsupportedEnformentMethod()

	def check(self, model, value):
		'''
		Constraints that implement this method can be checked
		natively (lol) before being committed to Postgres.
		Also gives the advantage of a single catch-all validation 
		(database validation will return errors one at a time as 
		it reaches them).
		:model The model object to which the check applies
		:value The value to check, for convience
		'''
		raise UnsupportedEnformentMethod()

	def check_and_throw(self, model, value):
		'''
		Calls `check()`, raising a `ValidationErrors`
		if the check fails. Will still raise an
		`UnsupportedEnforcementMethod` if `check()`
		is not implemented
		'''
		#	TODO: Integrate with check()
		if not self.check(model, value):
			raise ValidationErrors({
				self.target_column.name: self.error_message
			})

class RegexConstraint(Constraint):

	def __init__(self, name, error_msg, regex, ignore_case=False, negative=False):
		super().__init__(name, error_msg)
		self.regex = regex
		self.ignore_case = ignore_case
		self.negative = negative

	def as_client_parsable(self):
		as_flag = lambda b: '1' if b else '0'
		return f'regex:{quote(self.regex)}:{as_flag(self.ignore_case)}:{as_flag(self.negative)}'
	
	def as_sql(self):
		opr = '~'
		if self.negative:
			opr = f'!{opr}'
		if self.ignore_case:
			opr = f'{opr}*'
		col_ref = f'{self.target_column.model.__table__}.{self.target_column.name}'
		return f'CHECK ({col_ref} {opr} \'{self.regex}\')'

	def check(self, model, value):
		flags = re.I if self.ignore_case else 0
		return re.match(self.regex, value, flags=flags) is not None

class RangeConstraint(Constraint):
	#	TODO: Complex range constraints

	#	TODO: Allow either to be none in JS impl.
	def __init__(self, name, error_msg, max_value=None, min_value=None):
		super().__init__(name, error_msg)
		
		#	Assert validity
		if max_value is None and min_value is None:
			raise ColumnDefinitionError('Invalid range: none specified')

		self.max_value, self.min_value = max_value, min_value

	def as_client_parsable(self):
		max_ = 'null' if self.max_value is None else self.max_value
		min_ = 'null' if self.min_value is None else self.min_value
		return f'range:{min_},{max_}'

	def as_sql(self):
		col_ref = f'{self.target_column.model.__table__}.{self.target_column.name}'
		
		#	Create SQL
		ends = []
		if self.max_value is not None:
			ends.append(f'{col_ref} <= {self.max_value}')
		if self.min_value is not None:
			ends.append(f'{col_ref} >= {self.min_value}')
		ends = ' AND '.join(ends)

		return f'CHECK ({ends})'

class UniquenessConstraint(Constraint):

	def as_sql(self):
		return 'UNIQUE'

class NotNullConstraint(Constraint):

	def as_sql(self):
		return 'NOT NULL'
