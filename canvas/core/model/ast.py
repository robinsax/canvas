# coding: utf-8
'''
SQL statement abstract syntax tree primative and final nodes, as well as helper
methods. Contained interfaces are prefixed with I and mixins with M.
'''

from enum import Enum

class Comparator(Enum):
	'''The comparison operator enumerable.'''
	EQUALS				= '='
	NOT_EQUALS			= '<>'
	LESS				= '<'
	GREATER				= '>'
	LESS_OR_EQUAL		= '<='
	GREATER_OR_EQUAL	= '>='
	AND					= 'AND'
	OR					= 'OR'
	MATCHES				= '~'
	MATCHES_I			= '~*'

def nodeify(target, permit_strings=False):
	'''Return `target` as an AST node.'''
	if permit_strings and isinstance(target, str):
		return target
	if isinstance(target, Node):
		return target
	return Value(target)

def deproxy(target):
	'''Deproxy an AST node.'''
	from .model import Model

	if isinstance(target, type) and issubclass(target, Model):
		return target.__table__
	return target

def reproxy(target):
	'''Strictly reproxy an AST node proxy.'''
	from .tables import Table

	if isinstance(target, Table):
		return target.model_cls
	raise TypeError('Not an AST node proxy')

class Node:
	'''The root AST node type.'''

	def serialize(self, values=None):
		'''
		Return an SQL serialization of this AST node. `values` may be a list 
		for inserting literals. Since statements are always evaluated in-order,
		encountered literals should be appended to this list.

		On more complex `Node`s, where multiple serialization methods exists,
		this one should provide a *reference* to the node.
		'''
		raise NotImplementedError()

class ILiteral:
	'''A flag interface that informs eager bracket usage.'''
	pass

class ISelectable:
	'''
	An interface to be implemented by objects which can be the target of a 
	selection.
	'''

	def serialize_selection(self, name_policy=None):
		'''
		Return an SQL serialization of the selected columns or aggregators.
		If `name_policy` is not `None`, it will be a callable that must be
		passed the immediate host node and column for each column and return
		the required name of that column.
		'''
		raise NotImplementedError()

	def serialize_source(self, values=None):
		'''
		Return an SQL serialization of the source of this selection (i.e. the 
		table).
		'''
		raise NotImplementedError()
		
class IJoinable:
	'''
	An interface to be implemented by objects which can be join onto or can
	join other `IJoinable`s onto them.
	'''

	def join(self, other, condition=None, attr=None):
		'''Create a join of `other` onto this joinable.'''
		from .joins import Join
		
		return Join(self, other, condition, attr)

	#	TODO: Should live on ISelectable?
	def get_loader(self):
		'''
		Create or return a `Loader` for with which rows can be loaded from the
		selection of this joinable.
		'''
		raise NotImplementedError()

	def name_column(self, column):
		'''
		Return the name of the constituent `column` given that this joinable 
		is the immediate host.
		'''
		raise NotImplementedError()

	def get_columns(self):
		'''Return a list containing all constituent columns.'''
		raise NotImplementedError()

class ILoader:
	'''
	`ILoader`s are stateful objects that load models from rows selected with 
	`IJoinable`s. Packaged here despite being not strictly an abstract syntax 
	tree node. TODO: Review previous.
	'''

	def load_next(self, row_segment, session):
		'''Return a `row_segment` loaded onto its valid target.'''
		raise NotImplementedError()

class ScalarLoader(ILoader):
	'''A loader which simply returns the first value of the selection.'''

	def get_loader(self):
		return self

	def load_next(self, row_segment, session):
		return row_segment[0]

class MFlag:
	'''
	A mixin for exposed flag-like `Node`s which causes logical operator
	application to yield boolean `Comparison`s.
	'''
	# Default inverted to False here in the MRO.
	inverted = False

	def __and__(self, other):
		'''Return a conjunction of this `Node` with another.'''
		return Comparison(self, Comparator.AND, other)
	
	def __rand__(self, other):
		'''Return a conjunction of this `Node` with another.'''
		return Comparison(other, Comparator.AND, self)

	def __or__(self, other):
		'''Return a disjunction of this `Node` with another.'''
		return Comparison(self, Comparator.OR, other)

	def __ror__(self, other):
		'''Return a disjunction of this `Node` with another.'''
		return Comparison(other, Comparator.OR, self)

	def __invert__(self):
		'''
		Logically invert this flag. This is provided only for convience, 
		serialization methods must apply the inversion themselves.
		'''
		self.inverted = True
		return self

class MString:
	'''
	A mixin for exposed string-like `Node`s which enables string comparison
	operations.
	'''

	def __eq__(self, other):
		'''Return the equality of this `Node` with another.'''
		return Comparison(self, Comparator.EQUALS, other)

	def __ne__(self, other):
		'''Return the inequality of this `Node` with another.'''
		return Comparison(self, Comparator.NOT_EQUALS, other)
	
	def matches(self, regex, ignore_case=False):
		'''Return a regular expression match operation against this `Node`.'''
		oper = Comparator.MATCHES_I if ignore_case else Comparator.MATCHES
		return Comparison(self, oper, Literal(regex))

class MNumerical:
	'''
	A mixin for exposed numeric-like `Node`s which causes numerical comparison 
	operator application to yield `Comparison`s.
	'''

	def __eq__(self, other):
		'''Return the equality of this `Node` with another.'''
		return Comparison(self, Comparator.EQUALS, other)

	def __ne__(self, other):
		'''Return the inequality of this `Node` with another.'''
		return Comparison(self, Comparator.NOT_EQUALS, other)

	def __lt__(self, other):
		'''Return the 'less than' comparison of this `Node` with another.'''
		return Comparison(self, Comparator.LESS, other)

	def __le__(self, other):
		'''
		Return the 'less than or equal to' comparison of this `Node` with another.
		'''
		return Comparison(self, Comparator.LESS_OR_EQUAL, other)

	def __gt__(self, other):
		'''Return the 'greater than than' comparison of this `Node` with another.'''
		return Comparison(self, Comparator.GREATER, other)

	def __ge__(self, other):
		'''
		Return the 'greater than or equal to' comparison of this `Node` with another.
		'''
		return Comparison(self, Comparator.GREATER_OR_EQUAL, other)

class MAllTypes(MFlag, MNumerical, MString):
	'''A combination of the `MFlag`, `MNumerical`, and `MString` mixins.'''
	pass

class Literal(Node):
	'''A node containing a literal SQL string.'''

	def __init__(self, *parts, joiner=' '):
		'''
		::parts The parts of this SQL string to join.
		::joiner The string with which to join `parts`.
		'''
		parts = [nodeify(p, True) for p in parts]
		self.sql = joiner.join([p if isinstance(p, str) else p.serialize() for p in parts ])
	
	def serialize(self, values=None):
		'''Return the SQL represented by this literal node.'''
		return self.sql

class Value(Node, ILiteral, MAllTypes):
	'''A node containing a real value to be sanitized or inserted.'''

	def __init__(self, value):
		'''::value The value of any type.'''
		self.value = value

	def serialize(self, values=list()):
		'''Return the sanitized representation of this value or a format.'''
		#	Handle null or boolean values.
		if self.value is None:
			return 'NOT NULL' if self.inverted else 'NULL'
		if isinstance(self.value, bool):
			return 'FALSE' if self.inverted is self.value else 'TRUE'

		#	Use a format.
		values.append(self.value)
		return 'NOT %s' if self.inverted else '%s'

class ObjectReference(Node, ISelectable):
	'''
	An `ObjectReference` serializes into a reference to an in-database object.
	It must also be describable for creation.
	'''

	def __init__(self, object_type):
		'''::object_type The SQL name for this type of object.'''
		self.object_type = object_type

	def describe(self):
		'''
		Return an SQL serialization of the description of this object reference,
		to be used for it's creation.
		'''
		raise NotImplementedError()

class Comparison(Node, MFlag):
	'''A comparsion between two `Node`s with a given `Comparator`.'''

	def __init__(self, left, comparator, right):
		'''
		Create a comparison.
		::left The left side `Node` or nodeifiable.
		::comparator The `Comparator` to use.
		::right The right side `Node` or nodeifiable.
		'''
		self.left, self.right = nodeify(left), nodeify(right)
		self.comparator = comparator

		#	If both side are literal-esq, we can automatically group this
		#	comparison.
		self.is_grouped = (isinstance(self.left, ILiteral) and 
				isinstance(self.right, ILiteral))
	
	def serialize(self, values=list(), name_policy=None):
		'''Return the SQL serialization of this comparison.'''
		#	Resolve column names, preferring supplied policy.
		if name_policy:
			left, right = (
				name_policy(self.left, values), name_policy(self.right, values)
			)
		else:
			left, right = (
				self.left.serialize(values), self.right.serialize(values)
			)

		#	Create SQL, applying inversion and grouping.
		sql = ' '.join((left, self.comparator.value, right))
		if self.inverted:
			sql = 'NOT %s'%sql
		if self.is_grouped:
			sql = '(%s)'%sql
		return sql

	@property
	def grouped(self):
		'''
		Mutate this `Comparison` to be grouped upon access. Exposed as a 
		property for usage readability.
		'''
		self.is_grouped = True
		return self

class Aggregation(Node, ScalarLoader, ISelectable, ILiteral, MNumerical):
	'''A call to an in-database aggregator.'''

	def __init__(self, producer, source):
		'''
		Create an aggregation.
		::producer The in-database name of the aggregator.
		::source The source of the values to be aggregated (a column).
		'''
		self.producer, self.source = producer, nodeify(source)
	
	def serialize(self, values=list()):
		'''Serialize this aggregation as a call to an aggregator.'''
		return '%s(%s)'%(
			self.producer,
			self.source.serialize(values)
		)

	def serialize_selection(self, name_policy=None):
		return self.serialize()

	def serialize_source(self, values=list()):
		'''Serialize the source of this aggregation (the column's table).'''
		return self.source.table.serialize(values)

class Unique(Node, MFlag):
	'''A call to the unique operator on a set of columns.'''

	def __init__(self, *columns):
		self.columns = columns
	
	def serialize(self, values=None):
		return ' '.join((
			'UNIQUE (',
			', '.join(column.name for column in self.columns),
			')'
		))
