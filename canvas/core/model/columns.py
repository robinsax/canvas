#	coding utf-8
'''
Column and column type definitions.
'''

import re
import json
import uuid
import datetime as dt

from types import LambdaType

from ...exceptions import InvalidSchema
from ...namespace import export
from ...callbacks import (
	define_callback_type, 
	invoke_callbacks
)
from .sql_nodes import (
	SQLExpression,
	SQLComparison,
	SQLAggregatorCall
)
from . import _ResolveOther

_sentinel = object()
_column_types = dict()

define_callback_type('column_type_definition', arguments=[dict])

def define_column_types():
	_column_types.update({
		'int(?:eger)*': ('INTEGER', 'number'),
		'real|float': 'REAL',
		'serial': 'SERIAL',
		'bytes|blob': ('BYTEA', 'file'),
		'text': 'TEXT',
		'longtext': ('TEXT', 'textarea'),
		'json': 'JSON',
		'bool(?:ean)*':	('BOOLEAN', 'checkbox'),
		'uuid': ('CHAR(32)', 'text', lambda: uuid.uuid4()),
		'pw|pass(?:word)*': ('TEXT', 'password'),
		'^date$': ('DATE', 'date'),
		'^time$': ('TIME', 'time'),
		'dt|datetime': ('TIMESTAMP', 'datetime-local'),
		'(?:fk|foreign\s*key):(.+)': _sentinel
	})
	invoke_callbacks('column_type_definition', _column_types)

@export
class Column(SQLExpression):
	#	This is an expression because a column can be boolean.

	def __init__(self, type_str, constraints=[], default=_sentinel, primary_key=False):
		self.type_str = type_str

		self.constraints = constraints
		self.default, self.primary_key = default, primary_key

		self.type, self.model, self.name = (None,)*3
		self.sql_type, self.input_type = None, None
		self.is_fk, self.reference = False, None

	def resolve(self):
		#	Resolve type.
		for regex, data in _column_types.items():		
			match = re.match(regex, self.type_str, re.I)

			if match is not None:
				if data is _sentinel:
					#	Foreign key special case.
					target = match.group(1)
					try:
						#	Parse.
						target_table, target_column_name = target.split('.')
						target_table = _object_relational_map[target_table]
						target_column = target_table.__schema__[target_column_name]
					except:
						raise InvalidSchema('Malformed foreign key: %s'%self.reference_str)
					
					if not target_table.__created__:
						raise _ResolveOther(target_table)
					
					self.is_fk, self.reference = True, target_table
				else:
					#	Unpack definition.
					if isinstance(data, str):
						self.sql_type, self.input_type = data, 'text'
					elif len(data) == 3:
						self.sql_type, self.input_type, maybe_default = data
						if self.default is _sentinel:
							self.default = maybe_default
					else:
						self.sql_type, self.input_type = data
		
		if self.reference is None and self.sql_type is None:
			#	Neither a foreign key or regular column.
			raise InvalidSchema('Unknown column type: %s'%self.type_str)

		#	Resolve constraints.
		for constraint in self.constraints:
			constraint.resolve(self)

	def serialize(self, values=[]):			
		return '%s.%s'%(self.model.__table__, self.name)
		
	def get_default(self):
		if callable(self.default):
			return self.default()
		return self.default

	def value_for(self, model_obj):
		return getattr(model_obj, self.name)

	def set_value_for(self, model_obj, value):
		setattr(model_obj, self.name, value)

	def __eq__(self, other):
		return SQLComparison(self, other, '=')

	def __ne__(self, other):
		return SQLComparison(self, other, '<>')

	def __lt__(self, other):
		return SQLComparison(self, other, '<')

	def __le__(self, other):
		return SQLComparison(self, other, '<=')

	def __gt__(self, other):
		return SQLComparison(self, other, '>')

	def __ge__(self, other):
		return SQLComparison(self, other, '>=')

	def count(self):
		return SQLAggregatorCall('COUNT', self)

	def is_max(self):
		return SQLAggregatorCall('MAX', self)

	def is_min(self):
		return SQLAggregatorCall('MIN', self)

	def matches(self, other, ignore_case=False):
		return SQLComparison(self, other, '~*' if ignore_case else '~')
