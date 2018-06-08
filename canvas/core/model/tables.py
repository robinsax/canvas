#	coding utf-8
'''
The `Table` object definition.
'''

from collections import OrderedDict

from ...exceptions import InvalidSchema
from .ast import ObjectReference, ILoader, IJoinable
from .constraints import PrimaryKeyConstraint

#	Define the global table storage list, used for issuing creation.
_tables = list()

class Table(ObjectReference, IJoinable):
	'''
	`Table`s are joinable AST object references to in-database tables that 
	maintain and manage the database link for `Model`s. They are transparent 
	in most use-cases.
	'''
	
	def __init__(self, name, contents):
		'''
		Create a new representation of a table.
		::name The name of the table.
		::contents The dictionary passed to the `model` decorator containing
			the `Column`s and `Constraint`s of this table.
		'''
		super().__init__('TABLE')
		self.name = name
		self.constraints, self.columns = list(), OrderedDict()
		self.model_cls = None

		#	Unpack the schema dictionary and locate the primary key.
		self.primary_key = None
		for name, item in contents.items():
			item.name = name
			if isinstance(item, Constraint):
				self.constraints.append(item)
			else:
				for constraint in item.constraints:
					if isinstance(constraint, PrimaryKeyConstraint):
						if self.primary_key:
							raise InvalidSchema('Multiple primary keys for %s'%self.name)
						self.primary_key = item
				self.columns[name] = item
		#	Assert one was found.
		if not self.primary_key:
			raise InvalidSchema('No primary key for %s'%self.name)
		#	Ensure the primary key is the first entry within the column map.
		#	This invariant supports the Session class's functionality.
		self.columns.move_to_end(self.primary_key.name, False)

		#	Bind constituents.
		for item in self.columns.values():
			item.bind(self)
		for item in self.constraints:
			item.bind(self)

		#	Add this table to the master list.
		_tables.append(self)
	
	@classmethod
	def topo_order(cls):
		'''
		Return a topological sort of all tables, suitable for issuing creation
		SQL.
		'''
		#	Input and output.
		result, remaining = list(), list(_tables)
		#	State tracking.
		marked, tmp_marked = dict(), dict()

		#	Visit a single node.
		def visit(table):
			if table.name in marked:
				#	Already in output.
				return
			if table.name in tmp_marked:
				#	Revisiting before in output; cycle.
				raise InvalidSchema('Cyclic schema involving %s'%table.name)
			tmp_marked[table.name] = True
			
			#	Locate outgoing edges.
			for column in table.columns.values():
				if not isinstance(column.type, ForeignKeyColumnType):
					continue
				visit(column.type.target.table)

			#	Mark and insert in output.
			marked[table.name] = True
			result.append(table)

		#	Iterate input, visiting each.
		while remaining:
			visit(remaining.pop())
		
		#	Return output.
		return result

	def bind(self, model_cls):
		'''Bind onto a model class, attaching constituent columns.'''
		#	Link bidirectionally for de/re-proxying.
		model_cls.__table__ = self
		self.model_cls = model_cls

		#	Attach columns.
		for name, column in self.columns.items():
			setattr(model_cls, name, column)

	def get_columns(self):
		'''Return all non-lazy constituent columns.'''
		return (
			column for column in self.columns.values() if not column.type.lazy
		)

	def name_column(self, column):
		'''Trivially name a column.'''
		return column.name
	
	def serialize(self, values=None):
		'''Return a reference to this table.'''
		return self.name

	def serialize_source(self, values=None):
		'''Return a reference to this table.'''
		return self.name

	def serialize_selection(self, name_policy=None):
		'''
		Return a serialization of the columns in this table, honouring 
		`name_policy` if supplied.
		'''
		#	Lol.
		return ', '.join(
			((''.join((
				column.serialize(), ' AS %s'%(
					name_policy(column) if name_policy else str()
				)
			))) for column in self.get_columns())
		)

	def describe(self):
		'''Return the serialized description of this table.'''
		contents = (*self.columns.values(), *self.constraints)
		return ''.join((
			self.name, ' (',
			', '.join((item.describe() for item in contents)),
			')'
		))

class SimpleModelLoader(ILoader):
	'''The trivial model loader for loading models from a table.'''

	def __init__(self, table):
		self.table = table

	def load_next(self, row_segment, session):
		pass
