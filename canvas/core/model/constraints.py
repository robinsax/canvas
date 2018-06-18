# coding: utf-8
'''
Column and table constraint definitions.
'''

import re

from ...exceptions import InvalidSchema
from .ast import ObjectReference, Unique, MFlag, nodeify, reproxy

class Constraint(ObjectReference):
	'''
	The abstract base constraint class is an object reference AST `Node`.
	Whether a `Constraint` is table and/xor column level constraint is subclass
	specific.
	'''
	instances = dict()

	def __init__(self, postfix, error_message=None):
		'''
		Configure an overriding class.
		::postfix The unique to postfix for names of instances of this 
			constraint.
		::error_message The error message to display if the constraint
			is violated.
		'''
		super().__init__('CONSTRAINT')
		self.postfix, self.error_message = postfix, error_message
		self.host = self.name = None

	@classmethod
	def get(cls, name):
		'''Retrieve a constraint by name.'''
		return Constraint.instances.get(name)

	def bind(self, host):
		'''Bind this constraint to its host.'''
		self.host = host

		if not self.name:
			#	Generate a unique name for this constraint.
			self.name = '_'.join((
				host.serialize().replace('.', '_'), self.postfix
			))

		#	Register self.
		Constraint.instances[self.name] = self

	def precheck_violation(self, model, value):
		'''
		Evaluate whether this constraint is violated before before insertion 
		is attempted. If it is, return `True`. Implementation is optional.
		'''
		raise NotImplementedError()

	def validator_info(self):
		'''
		Return a dictionary containing a representation of this constraint that
		is understandable by a front-end validator.
		'''
		raise NotImplementedError()
	
	def describe(self):
		'''
		Serialize a description of this constraint. Sub-classes should 
		override `describe_rule` rather than this method.
		'''
		return ' '.join((
			'CONSTRAINT', self.name, self.describe_rule()
		))

	def describe_rule(self):
		'''Return a serialized description of this consraint rule.'''
		raise NotImplementedError()

	def serialize(self, values=None, name_policy=None):
		'''Serialize a reference to this constraint.'''
		return self.name

class CheckConstraint(Constraint):
	'''A generic `CHECK` constraint on a column or table.'''

	def __init__(self, error_message, condition_policy, name=None):
		'''
		Create a new check constraint. This should generally be done while 
		defining the attribute map of a model within it's decorator.

		::condition_policy A callable that will at some point be passed the
			host of this constraint to yeild a flag-like `Node`.
		::name The name of this constraint. If none is supplied, one will be
			automatically generated.
		'''
		super().__init__('check', error_message)
		self.condition_policy = condition_policy
		self.name = name

	def describe_rule(self):
		'''Serialize the policy-specified check for this constraint.'''
		#	Resolve the policy and assert it's result is valid.
		condition = nodeify(self.condition_policy(self.host.model_cls))
		if not issubclass(type(condition), MFlag):
			raise InvalidSchema(('Check constraint %s has non flag-like '
					+ 'condition')%self.name)
		
		#	Create and return the serialization. This is vulnerable to
		#	injection, but only from the caller itself.
		values = list()
		sql = condition.serialize(values)
		if not isinstance(condition, Unique):
			sql = ' '.join(('CHECK', sql))
		return sql%(*values,)

class PrimaryKeyConstraint(Constraint):
	'''A primary key constraint on a column.'''

	def __init__(self):
		super().__init__('pk')

	def describe_rule(self):
		return 'PRIMARY KEY'

class ForeignKeyConstraint(Constraint):
	'''A foreign key constraint on a column.'''

	def __init__(self, target):
		super().__init__('fk')
		self.target = target

	def describe_rule(self):
		return 'REFERENCES %s (%s)'%(
			self.target.table.name,
			self.target.name
		)

class NotNullConstraint(Constraint):
	'''A `NOT NULL` constraint on a column.'''

	def __init__(self, error_message='Required'):
		super().__init__('existance', error_message)

	def precheck_violation(self, model, value):
		return value is None

	def validator_info(self):
		return None
	
	def describe_rule(self):
		return 'NOT NULL'

class UniquenessConstraint(Constraint):
	'''A `UNIQUE` constraint on a column.'''

	def __init__(self, error_message='Must be unique'):
		super().__init__('uniqueness', error_message)
	
	def describe_rule(self):
		return 'UNIQUE'

class RegexConstraint(Constraint):
	'''A regular expression constraint.'''

	def __init__(self, error_message, regex, ignore_case=False, invert=False):
		super().__init__('format', error_message)
		self.regex = regex
		self.ignore_case, self.invert = ignore_case, invert

	def precheck_violation(self, model, value):
		return bool(re.match(self.regex, value)) == self.invert
	
	def describe_rule(self):
		opr = '~'
		if self.ignore_case:
			opr = ''.join((opr, '*'))
		if self.invert:
			opr = ''.join(('!', opr))
		
		return ' '.join((
			'CHECK (', 
				self.host.name, opr, 
				''.join(("'", self.regex.replace("'", "\'"), "'")),
			')'
		))
	
	def validator_info(self):
		return {
			'regex': self.regex,
			'ignore_case': self.ignore_case,
			'invert': self.invert
		}
