# coding: utf-8
'''
The `Join` AST node and API definition.
'''

from ...exceptions import InvalidQuery
from .ast import Node, ISelectable, IJoinable, deproxy, nodeify
from .columns import Column, ForeignKeyColumnType
from .tables import Table

class Join(Node, ISelectable, IJoinable):
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

		self.reset()
		self.set_name('_t')

	def reset(self):
		'''Reset this join's load state.'''
		#	Define some loading state attributes.
		self.source_obj = self.current_source_id = None

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
			if not self.condition:
				self.condition = nodeify(condition)
			else:
				self.condition &= nodeify(condition)
		
		#	Chain.
		return self
	
	#	TODO: Golf this method.
	def load_next(self, row_segment, session):
		'''
		Return the constituents of this join loaded onto `row_segment` or 
		return `None`.
		'''
		#	Check if the source model instance has changed.
		if row_segment[0] != self.current_source_id:
			if row_segment[0] is None:
				return None
			#	Create a new source model instance and store it's ID.
			self.source_obj = self.source.load_next(row_segment, session)
			self.current_source_id = row_segment[0]
		
		#	k tracks the current offset into the row segment.
		k = len(self.source.get_columns())
		#	Iterate destination constituents.
		for dest, attach_attr in zip(self.dests, self.attrs[1:]):
			#	Create the sub segment and check relation direction.
			sub_segment = row_segment[k:]
			link_column, is_one_attachment = self.find_link_column(dest)

			#	Allow the destination constituent to load the segment or 
			#	don't if
			if sub_segment[0] is not None:
				next_instance = dest.load_next(sub_segment, session)
			else:
				next_instance = None
			
			if not attach_attr:
				#	TODO: What do we want to do here?
				raise InvalidQuery(
					'No attachment attribute specified in join'
				)

			if not is_one_attachment:
				#	Assert the attachment array exists.
				if not hasattr(self.source_obj, attach_attr):
					setattr(self.source_obj, attach_attr, list())

				if next_instance:
					#	Check whether this is a reload and add to the 
					#	attaching array if not.
					attaching = getattr(self.source_obj, attach_attr)
					contains = False
					for item in attaching:
						if item is next_instance:
							contains = True
							break
					if not contains:
						attaching.append(next_instance)
			else:
				#	Directly attach the result.
				setattr(self.source_obj, attach_attr, next_instance)

			#	Increment k into the row segement.
			k += len(dest.get_columns())
			
		return self.source_obj

	def serialize(self, values=None, name_policy=None):
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
				'LEFT OUTER JOIN', dest.serialize_source(values),
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

		def query_name_policy(target, values=None):
			if isinstance(target, Column):
				return self.name_column(target, True)
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
					self.condition.serialize(values, name_policy=query_name_policy) if self.condition else 'TRUE'
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

	#	TODO: Golf.
	def name_column(self, column, for_query=False):
		'''Return the name of the constituent `column`.'''
		if for_query:
			if isinstance(self.source, Table) and self.source.contains_column(column):
				return '.'.join((self.source.name, self.source.name_column(column)))
			for dest in self.dests:
				if dest.contains_column(column):
					if isinstance(dest, Table):
						return '.'.join((dest.name, dest.name_column(column)))
					break
		return '_%s_%s'%(column.table.name, column.name)

	def get_columns(self):
		'''Return all constituent columns.'''
		dest_columns = list()
		for dest in self.dests:
			dest_columns.extend(dest.get_columns())
		return (*self.source.get_columns(), *dest_columns)
