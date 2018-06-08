#	coding utf-8
'''
The `Join` AST node and API definition.
'''

from .ast import ISelectable, IJoinable, ILoader, deproxy
from .columns import Column, ForeignKeyColumnType

class Join(Node, ISelectable, IJoinable, ILoader):
	'''
	`Join`s are selectable, joinable AST nodes. They represent the join of one
	or more destination joinables (tables or subsequent joins) onto a source
	joinable.
	'''

	def __init__(self, source, dest, condition=None, attr=None):
		'''
		Create a join. This should generally be done via the `Model` class 
		level `join` method.
		::source The source joinable.
		::dest An initial destination joinable.
		::condition A flag-like `Node` condition.
		::attr The name of the attribute upon which to load the joined model(s)
			of the initial destination joinable. If omitted, it will be inferred
			as the singular or plural form of the destination table, depending on
			the cardinality of it's relationship to the source joinable.
		'''
		self.source, self.dests = deproxy(source), [deproxy(dest)]
		self.attrs = [attr]
		self.condition = condition

		self.set_name('_t')

	def set_name(self, name):
		'''
		Set the reference name of this join, and subsequently its `Join` 
		children.
		'''
		self.name = name

		#	Rename child if it is a Join
		def maybe_rename(child, name):
			if isinstance(child, Join):
				child.set_name(name)

		#	Maybe rename each child.
		maybe_rename(self.source, '%s_s'%self.name)
		for i, dest in enumerate(self.dests):
			maybe_rename(dest, '%s_d_%d'%(self.name, i))

	def add(self, dest, condition=None, attr=None):
		'''
		Add another join destination. The parameters behave identically to 
		those of the constructor.
		'''
		#	Store the destination and attribute name.
		self.dests.append(deproxy(dest))
		self.attrs.append(attr)

		#	Update the condition if nessesary.
		if condition:
			self.condition &= nodeify(condition)
		
		#	Chain.
		return self

	def serialize(self, values=None):
		return self.name

	def serialize_selection(self, name_policy=None):
		'''
		Return the serialization of the columns in this join, honouring 
		`name_policy`if supplied.
		'''
		#	Return a reference to a column.
		def referenced(host, column):
			return '%s.%s%s'%(
				self.name, self.name_column(column), 
				(' AS %s'%name_policy(column) if name_policy else str())
			)

		#	Collect the destination references.
		dest_refs = list()
		for dest in self.dests:
			dest_refs.extend(referenced(dest, column) for column in dest.get_columns())
		
		#	Serialize and return.
		return ', '.join((
			*(referenced(self.source, column) for column in self.source.get_columns()),
			*dest_refs
		))

	def serialize_source(self, values=list()):
		'''Return the serialization the `JOIN` itself.'''
		#	Serialize a single destination as JOIN <x> ON <y>.
		def one_join(dest):
			#	Resolve the link and direction.
			link_column, reverse = self.find_link_column(dest)
			on_src, on_dest = (dest, self.source) if reverse else (self.source, dest)

			#	Serialize.
			return ' '.join((
				'JOIN', dest.serialize_source(values),
				'ON',
					'%s.%s'%(on_src.name, on_src.name_column(link_column)), '=', 
					'%s.%s'%(on_dest.name, on_dest.name_column(link_column.type.target))
			))

		#	Define the name policy.
		def name_policy(target, values=None):
			if isinstance(target, Column):
				return self.name_column(target)
			else:
				return target.serialize(values)

		#	Serialize and return.
		return ' '.join((
			'(',
				'SELECT', 
					', '.join([
						self.source.serialize_selection(name_policy),
						*(dest.serialize_selection(name_policy) for dest in self.dests)
					]),
				'FROM', 
					self.source.serialize_source(values), 
					*(one_join(dest) for dest in self.dests),
				'WHERE', (
					self.condition.serialize(values, name_policy=name_policy) if self.condition else 'TRUE'
				),
			') AS', self.name
		))

	def find_link_column(self, dest):
		'''
		Return a tuple containing the link column between the source and given 
		destination, as well as a flag indicating the link direction.
		'''
		source_columns, dest_columns = self.source.get_columns(), dest.get_columns()

		#	Check the source.
		for column in source_columns:
			typ = column.type
			if not isinstance(typ, ForeignKeyColumnType):
				continue
			for check_column in dest_columns:
				if check_column is typ.target:
					return column, False		

		#	Check the destination.
		for column in dest_columns:
			typ = column.type
			if not isinstance(typ, ForeignKeyColumnType):
				continue
			for check_column in source_columns:
				if check_column is typ.target:
					return column, True

		#	No link was found.
		raise InvalidQuery('No link between %s join %s'%(
			self.source.name, dest.name
		))

	def name_column(self, column):
		'''Return the name of the constituent `column`.'''
		return '_%s_%s'%(column.table.name, column.name)

	def get_columns(self):
		'''Return all constituent columns.'''
		dest_columns = list()
		for dest in self.dests:
			dest_columns.extend(dest.get_columns())
		return (*self.source.get_columns(), *dest_columns)
