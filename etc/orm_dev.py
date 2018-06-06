#	TODO Critial: No latebind
'''
	def fk_to(self, table):
		for column in self.columns:
			typ = column.type
			if isinstance(typ, ForeignKeyColumnType):
				if not typ.target.table is table:
					continue
				return column
		return None
'''

class CyclicSchema(Exception): pass

class InvalidForeignKey(Exception): pass

class InvalidQuery(Exception): pass

###

class Node:
	literal_esq = False

	def nodeify(self, target):
		if isinstance(target, Node):
			return target
		return Value(target)

	def serialize(self, values=list()):
		raise NotImplementedError()


class ISelectable:

	def serialize_selection(self):
		raise NotImplementedError()

	def serialize_source(self, values=tuple()):
		raise NotImplementedError()
		
class IJoinable:

	def join(self, other, condition=None):
		return Join(self, other, condition)

	def column_targets(self):
		raise NotImplementedError()

class ObjectReference(Node, ISelectable):#todo as interface?

	def __init__(self, object_type):
		self.object_type = object_type

	def describe(self):
		raise NotImplementedError()

###

class MFlag:
	inverted = False

	def __and__(self, other):
		return Comparison(self, 'AND', other)
	
	def __rand__(self, other):
		return Comparison(other, 'AND', self)

	def __or__(self, other):
		return Comparison(self, 'OR', other)

	def __ror__(self, other):
		return Comparison(other, 'OR', self)

	def __invert__(self):
		self.inverted = True
		return self

class MString:

	def __eq__(self, other):
		return Comparison(self, '=', other)

	def __ne__(self, other):
		return Comparison(self, '<>', other)
	
	def matches(self, other, ignore_case=False):
		return Comparison(self, '~*' if ignore_case else '~', other)

class MNumerical:

	def __eq__(self, other):
		return Comparison(self, '=', other)

	def __ne__(self, other):
		return Comparison(self, '<>', other)

	def __lt__(self, other):
		return Comparison(self, '<', other)

	def __le__(self, other):
		return Comparison(self, '<=', other)

	def __gt__(self, other):
		return Comparison(self, '>', other)

	def __ge__(self, other):
		return Comparison(self, '>=', other)

class MAllTypes(MFlag, MNumerical, MString): pass

###

class Literal(Node):

	def __init__(self, *parts):
		self.sql = ' '.join(parts)
	
	def serialize(self, values=None):
		return self.sql

class Value(Node, MAllTypes):
	literal_esq = True

	def __init__(self, value):
		self.value = value

	def serialize(self, values=list()):
		if self.value is None:
			return 'NOT NULL' if self.inverted else 'NULL'
		if isinstance(self.value, bool):
			return 'FALSE' if self.inverted is self.value else 'TRUE'

		values.append(self.value)
		return 'NOT %s' if self.inverted else '%s'

class Comparison(Node, MFlag):

	def __init__(self, left, operator, right):
		self.left, self.right = self.nodeify(left), self.nodeify(right)
		self.operator = operator

		self.is_grouped = self.left.literal_esq and self.right.literal_esq
	
	def serialize(self, values=list()):
		sql = ' '.join([
			self.left.serialize(values),
			self.operator,
			self.right.serialize(values)
		])
		sql = 'NOT %s'%sql if self.inverted else sql
		sql = '(%s)'%sql if self.is_grouped else sql
		return sql

	@property
	def grouped(self):
		self.is_grouped = True
		return self

class Aggregation(Node, MNumerical, ISelectable):
	literal_esq = True

	def __init__(self, producer, source):
		self.producer, self.source = producer, self.nodeify(source)
	
	def serialize(self, values=list()):
		return '%s(%s)'%(
			self.producer,
			self.source.serialize(values)
		)

	def serialize_selection(self):
		return self.serialize()

	def serialize_source(self, values=list()):
		return self.source.table.serialize(values)

###

class ColumnType:

	def __init__(self, typ):
		self.type = typ

	def bind(self, host):
		pass

	def late_bind(self, column):
		pass

	def describe(self):
		return self.type

class ForeignKeyColumnType(ColumnType):

	def __init__(self, target_ref):
		self.target_ref = target_ref
		self.target = None

	def late_bind(self, column):
		target_table, target_column = self.target_ref.split('.')
		for table in _tables:
			if table.name != target_table:
				continue
			for c in table.columns:
				if c.name == target_column:
					self.target = c
					break
		
		if not self.target:
			raise InvalidForeignKey('No such target %s'%self.target_ref)

		column.add_constraint(ForeignKeyConstraint(self.target))

	def describe(self):
		return self.target.type.describe()

#	TODO
def resolve_type(typ):
	if typ.startswith('fk:'):
		return ForeignKeyColumnType(typ[3:])
	return ColumnType(typ)

###

class Constraint(ObjectReference):

	def __init__(self, postfix):
		super().__init__('CONSTRAINT')
		self.postfix = postfix
		self.host = self.name = None

	def bind(self, host):
		self.host = host
		if not self.name:
			self.name = '_'.join((host.serialize().replace('.', '_'), self.postfix))
	
	def describe(self):
		return ' '.join((
			'CONSTRAINT', self.name, self.describe_rule()
		))

	def describe_rule(self):
		raise NotImplementedError()

	def serialize(self, values=list()):
		return self.name

class CheckConstraint(Constraint):

	def __init__(self, condition, name=None):
		super().__init__('check')
		self.name = name
		self.condition = condition

	def describe_rule(self):
		values = list()
		sql = self.nodeify(self.condition(self.host)).serialize(values)
		return ' '.join(('CHECK', sql%tuple(values)))

class PrimaryKeyConstraint(Constraint):

	def __init__(self):
		super().__init__('pk')

	def describe_rule(self):
		return 'PRIMARY KEY'

class ForeignKeyConstraint(Constraint):

	def __init__(self, target):
		super().__init__('fk')
		self.target = target

	def describe_rule(self):
		return 'FOREIGN KEY REFERENCES %s (%s)'%(
			self.target.table.name,
			self.target.name
		)

###

class Column(ObjectReference, MAllTypes):
	object_type = 'COLUMN'
	literal_esq = True

	def __init__(self, name, typ, *constraints):
		self.name, self.type = name, resolve_type(typ)
		self.table = None
		self.constraints = list(constraints)

	@property
	def safe_name(self):
		return '_'.join((self.table.name, self.name))

	def bind(self, table):
		self.table = table
		self.type.bind(self)

		for constraint in self.constraints:
			constraint.bind(self)		

	def add_constraint(self, constraint):
		self.constraints.append(constraint)
		constraint.bind(self)

	def serialize_selection(self):
		return self.name

	def serialize_source(self, values=tuple()):
		return self.table.name

	def serialize(self, values=list()):
		return '.'.join((self.table.name, self.name))
	
	def describe(self):
		return ' '.join((
			self.name,
			self.type.describe(),
			*[constraint.describe() for constraint in self.constraints]
		))

	def max(self):
		return Aggregation('MAX', self)

	def min(self):
		return Aggregation('MIN', self)

class ColumnTarget:

	def __init__(self, column, name):
		self.column, self.name = column, name

###

class Join(IJoinable):

	def __init__(self, left, right, condition):
		self.left, self.right = left, right
		self.condition = condition

	def column_targets(self):
		return (*self.left.column_targets, *self.right.column_targets)

###

_tables = list()
class Table(ObjectReference):

	def __init__(self, name, *contents):
		super().__init__('TABLE')
		self.name = name
		self.constraints, self.columns = list(), list()

		for item in contents:
			if isinstance(item, Constraint):
				self.constraints.append(item)
			else:
				self.columns.append(item)

		for item in self.columns:
			item.bind(self)
		for item in self.constraints:
			item.bind(self)
	
		_tables.append(self)

	def __hash__(self):
		return hash(self.name)

	def __eq__(self, other):
		return self.name == other.name

	def contains_column(self, column):
		for check in self.columns:
			if check is column:
				return True
		return False

	def link_column(self, joinable):
		for column in self.columns:
			if not isinstance(column.type, ForeignKeyColumnType):
				continue
			typ = column.type
			if joinable.contains_column(typ.target):
				return column
		return None

	def serialize(self, values=tuple()):
		return self.name

	def serialize_selection(self):
		return ', '.join((column.serialize() for column in self.columns))

	def serialize_source(self, values=tuple()):
		return self.name

	def describe(self):
		contents = (*self.columns, *self.constraints)
		return ''.join((
			self.name, ' (\n\t',
			',\n\t'.join((item.describe() for item in contents)),
			'\n)'
		))

def order_tables():
	result, remaining = list(), list(_tables)
	marked, tmp_marked = dict(), dict()

	def visit(table):
		if table in marked:
			return
		if table in tmp_marked:
			raise CyclicSchema()
		tmp_marked[table] = True
		
		for column in table.columns:
			if not isinstance(column.type, ForeignKeyColumnType):
				continue
			visit(column.type.target.table)

		marked[table] = True
		result.insert(0, table)

	while remaining:
		visit(remaining.pop())
	
	return reversed(result)

###

def create(target):
	sql = ' '.join((
		'CREATE', target.object_type, 'IF NOT EXISTS',
		target.describe(),
		';'
	))
	return sql, tuple()

def select(target, condition):
	values = list()
	sql = ' '.join([
		'SELECT', target.serialize_selection(),
		'\n\tFROM', target.serialize_source(values),
		'\n\tWHERE', condition.serialize(values),
		';'
	])

	return sql, values

t3 = Table('test3', 
	Column('b', 'TIMESTAMP'),
	Column('a_ref', 'fk:test2.a')
)
t4 = Table('test4', 
	Column('b_ref', 'fk:test3.b')
)
t2 = Table('test2',
	Column('a', 'THING'),
	Column('x_ref', 'fk:test.x'),	
	CheckConstraint(lambda t: True, 'always')
)
t = Table('test',
	Column('x', 'INT', CheckConstraint(lambda x: x < 10)),
	Column('y', 'SERIAL', PrimaryKeyConstraint()),	
	CheckConstraint(lambda t: False, 'never')
)

for t in _tables:
	for c in t.columns:
		c.type.late_bind(c)

print('\n'.join([create(t)[0] for t in order_tables()]))

class TestModel:

	def __init__(self, table):
		self.__table__ = table

		for column in table.columns:
			setattr(self, column.name, column)

m1 = TestModel(t)
m2 = TestModel(t2)
m3 = TestModel(t3)
m4 = TestModel(t4)

print(select(m1.x.max(), m1.y < 2))
print(select(m1.__table__, m1.x > 100))
