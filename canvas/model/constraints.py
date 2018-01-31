#	coding utf-8
'''
Column-value constraint representations.
'''

import re

from urllib.parse import quote

from ..exceptions import (
	ColumnDefinitionError, 
	UnsupportedEnforcementMethod,
	ValidationErrors
)

__all__ = [
	'get_constraint',
	'Constraint',
	'RegexConstraint',
	'RangeConstraint',
	'UniquenessConstraint',
	'NotNullConstraint'
]

#	The constraint name to constraint object mapping used for lookup in 
#	native-evaluation and serialization for client side evaluation.
_constraint_map = {}

def get_constraint(name):
	'''
	Return the constraint object with name `name`, or `None` if there isn't 
	one.
	'''
	return _constraint_map.get(name, None)

class Constraint:
	'''
	Base constraint class enforces a name, error message and placeholder 
	evaluation methods.
	'''

	#	TODO: A class attribute might be better for name_postfix.
	def __init__(self, name_postfix, error_message):
		'''
		Define a new constraint type.

		:name_postfix A unique name postfix for the overriding constraint type.
		:error_message A human-readable error message to provide when this 
			constraint is violated.
		'''
		self.name_postfix, self.error_message = name_postfix, error_message

		#	Store placeholder values.
		self.column, self.name = (None,)*2

	def resolve(self, column):
		'''
		Resolve this constraint as belonging to `Column`.
		'''
		#	Store the column.
		self.column = column
		#	Populate the name.
		self.name = f'{column.model.__table__}_{column.name}_{self.name_postfix}'

		#	Register self for created the name.
		_constraint_map[self.name] = self
	
	def as_client_parsable(self):
		'''
		Return a client-parsable representation of this constraint for 
		client-side validation.

		The representation should be of the format `type_name:representation`.

		A front-end validation method must then exist for `type_name`.
		'''
		raise UnsupportedEnforcementMethod()

	def as_sql(self):
		'''
		Return an SQL serialization of this constraint.
		'''
		raise UnsupportedEnforcementMethod()

	def check(self, model, value):
		'''
		Return whether or not the constraint is met by the given input, or 
		raise an `UnsupportedEnforcementMethod`.
		
		Implementing this method allows a single catch-all validation as 
		opposed to the one-at-a-time validation of Postgres.

		:model The model object to which the check applies.
		:value The value to check, for convience.
		'''
		raise UnsupportedEnforcementMethod()

	def check_with_throw(self, model, value):
		'''
		Call `check()` and raise a `ValidationErrors` if the check fails. Will 
		raise an `UnsupportedEnforcementMethod` if `check()` is not implemented.

		Note a `ValidationErrors` will cause a canonical failure response to be 
		sent to the client.
		'''
		if not self.check(model, value):
			raise ValidationErrors({
				self.column.name: self.error_message
			})

class RegexConstraint(Constraint):
	'''
	A regular expression constraint on textual columns.
	'''

	def __init__(self, error_message, regex, ignore_case=False, negative=False):
		'''
		Create a new regular expression constraint.

		:error_message A human-readable error message to provide when this 
			constraint is violated.
		:regex The regular expression which the column values must match.
		:ignore_case Whether the regular expression should be 
			case-insensitive.
		:negative Whether this constraint enforces the column value does *not* 
			match `regex`.
		'''
		super().__init__('format', error_message)
		self.regex = regex
		self.ignore_case, self.negative = ignore_case, negative

	def as_client_parsable(self):
		'''
		Return a client parsable representation of this regular expression 
		constraint.
		'''
		as_flag = lambda b: '1' if b else '0'

		return f'regex:{quote(self.regex)}:{as_flag(self.ignore_case)}:{as_flag(self.negative)}'
	
	def as_sql(self):
		'''
		Return an SQL representation of this regular expression constraint.
		'''
		opr = '~'
		if self.negative:
			opr = f'!{opr}'
		if self.ignore_case:
			opr = f'{opr}*'
		return f'CHECK ({self.column.serialize([])} {opr} \'{self.regex}\')'

	def check(self, model, value):
		'''
		Evaluate whether `value` satisfies this regular expression constraint.
		'''
		flags = re.I if self.ignore_case else 0
		return re.match(self.regex, value, flags=flags) is not None

class RangeConstraint(Constraint):
	'''
	A range constraint on numerical columns.
	'''
	#	TODO: Support all permutation of above and below constraint presence on the 
	#	client side.

	def __init__(self, error_message, max_value=None, min_value=None):
		'''
		Create a new regular expression constraint.

		:error_message A human-readable error message to provide when this 
			constraint is violated.
		:max_value The maximum value enforced by this constraint.
		:min_value The minimum value enforced by this constraint.
		'''
		super().__init__('range', error_message)
		
		#	Assert range validity.
		if max_value is None and min_value is None:
			raise ColumnDefinitionError('Invalid range: none specified')
		if (max_value is not None and min_value is not None 
				and max_value <= min_value):
			raise ColumnDefinitionError('Invalid range: empty')

		self.max_value, self.min_value = max_value, min_value

	def as_client_parsable(self):
		'''
		Return a client parsable representation of this numerical constraint.
		'''
		max_ = 'null' if self.max_value is None else self.max_value
		min_ = 'null' if self.min_value is None else self.min_value
		return f'range:{min_},{max_}'

	def as_sql(self):
		'''
		Return an SQL representation of this numerical constraint.
		'''
		#	Create the column reference SQL.
		col_ref = self.column.serialize([])
		
		#	Create comparison SQL.
		ends = []
		if self.max_value is not None:
			ends.append(f'{col_ref} <= {self.max_value}')
		if self.min_value is not None:
			ends.append(f'{col_ref} >= {self.min_value}')
		ends = ' AND '.join(ends)

		return f'CHECK ({ends})'

class UniquenessConstraint(Constraint):
	'''
	A constraint that enforces column value uniqueness.
	'''

	def __init__(self, error_message='Must be unique'):
		super().__init__('uniqueness', error_message)

	def as_sql(self):
		return 'UNIQUE'

class NotNullConstraint(Constraint):
	'''
	A constraint that enforces non-null column value.
	'''

	def __init__(self, error_message='Required'):
		super().__init__('existance', error_message)

	def as_sql(self):
		return 'NOT NULL'
