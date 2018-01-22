#	coding utf-8
'''
Column-value constraint representations.
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

#	The constraint name to constraint object mapping used
#	for lookup in native-evaluation and for-client 
#	serialization.
_constraint_map = {}

def get_constraint(name):
	'''
	Return the constraint object with name `name`, or 
	`None` if there isn't one.
	'''
	return _constraint_map.get(name, None)

class Constraint:
	'''
	Base constraint class enforces a name, error message,
	and placeholder evaluation methods.
	'''

	def __init__(self, name, error_message):
		'''
		Define a new constraint type.

		:name A unique name for this constraint.
		:error_message A human-readable error message to 
			provide when this constraint is violated.
		'''
		self.name, self.error_message = name, error_message

		#	Store a placeholder value for the targeted column
		#	object.
		self.target_column = None

		#	Add to the constraint name to constraint object 
		#	mapping.
		_constraint_map[name] = self
	
	def as_client_parsable(self):
		'''
		Return a client-parsable representation of this
		constraint for client-side validation.

		The representation should be of the format 
		`type_name:representation`.

		A front-end validation method must then exist for 
		`type_name`.
		'''
		raise UnsupportedEnformentMethod()

	def as_sql(self):
		'''
		Return an SQL serialization of this constraint.
		'''
		raise UnsupportedEnformentMethod()

	def check(self, model, value):
		'''
		Return whether or not the constraint is met by the
		given input, or raise an `UnsupportedEnforcementMethod`.
		
		Implementing this method allows a single catch-all validation
		as opposed to the one-at-a-time validation of Postgres.

		:model The model object to which the check applies.
		:value The value to check, for convience.
		'''
		raise UnsupportedEnformentMethod()

	def check_with_throw(self, model, value):
		'''
		Call `check()` and raise a `ValidationErrors` if the check 
		fails. Will raise an `UnsupportedEnforcementMethod` if 
		`check()` is not implemented.

		Note a `ValidationErrors` will cause a canonical failure 
		response to be sent to the client.
		'''
		if not self.check(model, value):
			raise ValidationErrors({
				self.target_column.name: self.error_message
			})

class RegexConstraint(Constraint):
	'''
	A regular expression constraint on textual columns.
	'''

	def __init__(self, name, error_message, regex, ignore_case=False, negative=False):
		'''
		Create a new regular expression constraint.

		:name A unique name for this constraint.
		:error_message A human-readable error message to 
			provide when this constraint is violated.
		:regex The regular expression which the column values
			must match.
		:ignore_case Whether the regular expression should be
			case-insensitive.
		:negative Whether this constraint enforces the column
			value does *not* match `regex`.
		'''
		super().__init__(name, error_message)
		self.regex = regex
		self.ignore_case, self.negative = ignore_case, negative

	def as_client_parsable(self):
		'''
		Return a client parsable representation of this
		regular expression constraint.
		'''
		as_flag = lambda b: '1' if b else '0'

		return f'regex:{quote(self.regex)}:{as_flag(self.ignore_case)}:{as_flag(self.negative)}'
	
	def as_sql(self):
		'''
		Return an SQL representation of this regular
		expression.
		'''
		opr = '~'
		if self.negative:
			opr = f'!{opr}'
		if self.ignore_case:
			opr = f'{opr}*'
		col_ref = f'{self.target_column.model.__table__}.{self.target_column.name}'
		return f'CHECK ({col_ref} {opr} \'{self.regex}\')'

	def check(self, model, value):
		'''
		Evaluate whether `value` satisfies this regular 
		expression constraint.
		'''
		flags = re.I if self.ignore_case else 0
		return re.match(self.regex, value, flags=flags) is not None

class RangeConstraint(Constraint):
	'''
	A range constraint on numerical columns.

	TODO: Support all permutation of above and below
		constraint presence on the client side.
	'''

	def __init__(self, name, error_message, max_value=None, min_value=None):
		'''
		Create a new regular expression constraint.

		:name A unique name for this constraint.
		:error_message A human-readable error message to 
			provide when this constraint is violated.
		:max_value The maximum value enforced by this constraint.
		:min_value The minimum value enforced by this constraint.
		'''
		super().__init__(name, error_message)
		
		#	Assert range validity.
		if max_value is None and min_value is None:
			raise ColumnDefinitionError('Invalid range: none specified')
		if (max_value is not None and min_value is not None 
				and max_value <= min_value):
			raise ColumnDefinitionError('Invalid range: empty')

		self.max_value, self.min_value = max_value, min_value

	def as_client_parsable(self):
		'''
		Return a client parsable representation of this 
		numerical constraint.
		'''
		max_ = 'null' if self.max_value is None else self.max_value
		min_ = 'null' if self.min_value is None else self.min_value
		return f'range:{min_},{max_}'

	def as_sql(self):
		'''
		Return an SQL representation of this numerical
		constraint.
		'''
		#	Create the column reference SQL.
		col_ref = f'{self.target_column.model.__table__}.{self.target_column.name}'
		
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
	A constraint that enforces column value 
	uniqueness.
	'''

	def as_sql(self):
		return 'UNIQUE'

class NotNullConstraint(Constraint):
	'''
	A constraint that enforces non-null column
	value.
	'''

	def as_sql(self):
		return 'NOT NULL'
