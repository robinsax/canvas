#	TODO Critial: No latebind

class CyclicSchema(Exception): pass

class InvalidForeignKey(Exception): pass

class InvalidQuery(Exception): pass

###
def nodeify(target):
	if isinstance(target, Node):
		return target
	return Value(target)

class Node:
	literal_esq = False

	def serialize(self, values=None):
		raise NotImplementedError()


class ISelectable:

	def serialize_selection(self, name_policy=None):
		raise NotImplementedError()

	def serialize_source(self, values=tuple()):
		raise NotImplementedError()
		
class IJoinable:

	def join(self, other, condition=None):
		return Join(self, other, condition)

	def name_column(self, column):
		raise NotImplementedError()

	def get_columns(self):
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
		self.left, self.right = nodeify(left), nodeify(right)
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
		self.producer, self.source = producer, nodeify(source)
	
	def serialize(self, values=list()):
		return '%s(%s)'%(
			self.producer,
			self.source.serialize(values)
		)

	def serialize_selection(self, name_policy=None):
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
		sql = nodeify(self.condition(self.host)).serialize(values)
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

	def bind(self, table):
		self.table = table
		self.type.bind(self)

		for constraint in self.constraints:
			constraint.bind(self)		

	def add_constraint(self, constraint):
		self.constraints.append(constraint)
		constraint.bind(self)

	def serialize_selection(self):
		return '%s.%s'%(self.table.name, self.name)

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

	def __repr__(self):
		return '<Column %s (of %s)>'%(self.name, self.table.name if self.table else 'none')

class ColumnTarget:

	def __init__(self, column, name):
		self.column, self.name = column, name

###

class Join(Node, ISelectable, IJoinable):

	def __init__(self, left, right, condition):
		self.left, self.right = left, right
		self.condition = condition
		self.link_column, self.is_rtl = self.find_link_column()

		self.set_name('_t')

	def set_name(self, name):
		self.name = name

		if isinstance(self.left, Join):
			self.left.set_name('%s_l'%name)
		if isinstance(self.right, Join):
			self.right.set_name('%s_r'%name)

	def serialize(self, values=None):
		return self.name

	def serialize_selection(self, name_policy=None):
		def referenced(host, column):
			return '%s.%s%s'%(
				self.name, self.name_column(column), 
				(' AS %s'%name_policy(column) if name_policy else str())
			)
		
		return ', '.join((
			*(referenced(self.right, column) for column in self.right.get_columns()),
			*(referenced(self.left, column) for column in self.left.get_columns())
		))

	def serialize_source(self, values=list()):
		from_host, to_host = (self.right, self.left) if self.is_rtl else (self.left, self.right)
		join_condition = ' '.join((
			#	TODO: name_column should take with_self flag
			'%s.%s'%(from_host.name, from_host.name_column(self.link_column)), '=', 
			'%s.%s'%(to_host.name, to_host.name_column(self.link_column.type.target))
		))
		name_policy = lambda c: self.name_column(c)

		return ' '.join((
			'( SELECT', 
				self.left.serialize_selection(name_policy), ',', 
				self.right.serialize_selection(name_policy),
			'FROM', 
				self.left.serialize_source(values), 'JOIN',
				self.right.serialize_source(values),
			'ON', join_condition, ') AS', self.name
		))

	def find_link_column(self):
		left_columns, right_columns = self.left.get_columns(), self.right.get_columns()
		for column in left_columns:
			typ = column.type
			if not isinstance(typ, ForeignKeyColumnType):
				continue
			for right_column in right_columns:
				if right_column is typ.target:
					return column, False				

		for column in right_columns:
			typ = column.type
			if not isinstance(typ, ForeignKeyColumnType):
				continue
			for left_column in left_columns:
				if left_column is typ.target:
					return column, True	

		raise InvalidQuery('No link between %s join %s'%(
			self.left.name, self.right.name
		))

	def name_column(self, column):
		return '_%s_%s'%(column.table.name, column.name)

	def get_columns(self):
		return (*self.left.get_columns(), *self.right.get_columns())

###

_tables = list()
class Table(ObjectReference, IJoinable):

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

	def get_columns(self):
		return self.columns

	def name_column(self, column):
		return column.name
	
	def __hash__(self):
		return hash(self.name)

	def __eq__(self, other):
		return self.name == other.name

	def serialize(self, values=tuple()):
		return self.name

	def serialize_selection(self, name_policy=None):
		return ', '.join(
			((
				'%s%s'%(column.serialize(), ' AS %s'%name_policy(column) if name_policy else str())
			) for column in self.columns)
		)

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
		'FROM', target.serialize_source(values),
		'WHERE', nodeify(condition).serialize(values),
		';'
	])

	return sql, values
##









####
users = Table('users',
	Column('id', 'UUID', PrimaryKeyConstraint()),
	Column('name', 'TEXT', CheckConstraint(lambda x: x < 10)),
	Column('organization_id', 'fk:organizations.id')
)
countries = Table('countries', 
	Column('id', 'UUID', PrimaryKeyConstraint()),
	Column('name', 'TEXT')
)
orgs = Table('organizations',
	Column('id', 'UUID', PrimaryKeyConstraint()),
	Column('name', 'TEXT'),
	Column('country_id', 'fk:countries.id')
)



for t in _tables: #TODO nononononono
	for c in t.columns:
		c.type.late_bind(c)

print(*[create(t)[0] for t in order_tables()])





j = users.join(orgs)
j2 = countries.join(j)
print(select(j2, True)[0])
