#	TODO Critial: No latebind

class InvalidSchema(Exception): pass

class InvalidForeignKey(Exception): pass

class InvalidQuery(Exception): pass

###
def nodeify(target):
	if isinstance(target, Node):
		return target
	return Value(target)

def deproxy(target):
	if isinstance(target, object.__class__) and issubclass(target, Model):
		return target.__table__
	return target

class Node:
	literal_esq = False

	def serialize(self, values=None):
		raise NotImplementedError()

class Statement:

	def write(self):
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
	
	def serialize(self, values=list(), name_policy=None):
		if name_policy:
			left, right = name_policy(self.left, values), name_policy(self.right, values)
		else:
			left, right = self.left.serialize(values), self.right.serialize(values)

		sql = ' '.join((left, self.operator, right))
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

	def __init__(self, lazy):
		self.lazy = lazy

	def bind(self, host):
		pass

	def late_bind(self, column):
		pass

	def describe(self):
		return self.type

class BasicColumnType(ColumnType): # singleton

	def __init__(self, typ, input_type='text', default_policy=None, lazy=False):
		super().__init__(lazy)
		self.type, self.input_type = typ, input_type
		self.default_policy = default_policy

class ForeignKeyColumnType(ColumnType):

	def __init__(self, target_ref):
		super().__init__(False)
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

_type_map = {
	'int(?:eger)*': BasicColumnType('INTEGER', 'number'),
	'real|float': BasicColumnType('REAL'),
	'serial': BasicColumnType('SERIAL'),
	'text': BasicColumnType('TEXT'),
	'longtext': BasicColumnType('TEXT', 'textarea'),
	'bool(?:ean)*':	BasicColumnType('BOOLEAN', 'checkbox'),
	'uuid': BasicColumnType('CHAR(32)', 'text', lambda: uuid.uuid4()),
	'pw|pass(?:word)*': BasicColumnType('TEXT', 'password'),
	'date$': BasicColumnType('DATE', 'date'),
	'time$': BasicColumnType('TIME', 'time'),
	'dt|datetime': BasicColumnType('TIMESTAMP', 'datetime-local'),
	'json': BasicColumnType('JSON', lazy=True)
}

import re
def resolve_type(typ):
	if typ.startswith('fk:'):
		return ForeignKeyColumnType(typ[3:])
	for regex, checked_typ in _type_map.items():
		if re.match(regex, typ):
			return checked_typ
	raise InvalidSchema('Invalid type definition %s'%typ)

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

	def __init__(self, typ, *constraints):
		self.name, self.type = None, resolve_type(typ)
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

###

class Join(Node, ISelectable, IJoinable):

	def __init__(self, left, right, condition):
		self.left, self.right = deproxy(left), deproxy(right)
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

		def name_policy(target, values=None):
			if isinstance(target, Column):
				return self.name_column(target)
			else:
				return target.serialize(values)

		return ' '.join((
			'(',
				'SELECT', 
					self.left.serialize_selection(name_policy), ',', 
					self.right.serialize_selection(name_policy),
				'FROM', 
					self.left.serialize_source(values), 'JOIN',
					self.right.serialize_source(values),
				'ON', join_condition, 
				'WHERE', (
					self.condition.serialize(values, name_policy=name_policy) if self.condition else 'TRUE'
				),
			') AS', self.name
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

	def __init__(self, name, contents):
		super().__init__('TABLE')
		self.name = name
		#	TODO: COLUMNs as ordereddict
		self.column_names, self.constraints, self.columns = list(), list(), list()

		for name, item in contents.items():
			item.name = name
			if isinstance(item, Constraint):
				self.constraints.append(item)
			else:
				self.columns.append(item)
				self.column_names.append(item)

		for item in self.columns:
			item.bind(self)
		for item in self.constraints:
			item.bind(self)
	
		_tables.append(self)

	def bind(self, model_cls):
		model_cls.__table__ = self

		for column in self.columns:
			setattr(model_cls, column.name, column)

	def get_columns(self):
		return [column for column in self.columns if not column.type.lazy]

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
			) for column in self.get_columns())
		)

	def serialize_source(self, values=tuple()):
		return self.name

	def describe(self):
		contents = (*self.columns, *self.constraints)
		return ''.join((
			self.name, ' (',
			', '.join((item.describe() for item in contents)),
			')'
		))

def order_tables():
	result, remaining = list(), list(_tables)
	marked, tmp_marked = dict(), dict()

	def visit(table):
		if table in marked:
			return
		if table in tmp_marked:
			raise InvalidSchema('Cyclic schema involving %s'%table.name)
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

class CreateStatement(Statement):

	def __init__(self, target):
		self.target = deproxy(target)

	def write(self):
		return ' '.join((
			'CREATE', self.target.object_type, 'IF NOT EXISTS',
				self.target.describe()
		)), tuple()

class SelectStatement(Statement):

	def __init__(self, target, condition=True):
		self.target = deproxy(target)
		self.condition = nodeify(condition)

	def write(self):
		values = list()
		sql = ' '.join((
			'SELECT', self.target.serialize_selection(),
			'FROM', self.target.serialize_source(values),
			'WHERE', nodeify(self.condition).serialize(values)
		))
		return sql, values

##


def exec_statement(statement):
	sql, values = statement.write()
	print(sql + ';')
	print(values)


####

class Model:
	__table__ = None
	__session__ = None
	__dirty__ = dict()

	def __loaded__(self, session):
		self.__dirty__ = dict()
		self.__session__ = session

	def __getattribute__(self, key):
		cls = super().__getattribute__('__class__')
		if super().__getattribute__('__session__') and key in cls.__table__.column_names:
			exec_statement(SelectStatement(getattr(cls, key), getattr(cls, 'id') == 1))
			return 'TODO'

		return super().__getattribute__(key)

	def __setattr__(self, key, value):
		if key in self.__table__.column_names: #todo no
			if key not in self.__dirty__:
				self.__dirty__[key] = value

		return super().__setattr__(key, value)

	@classmethod
	def join(cls, other, condition=None):
		return cls.__table__.join(other, condition)
	
def model(table_name, contents):
	def model_inner(cls):
		table = Table(table_name, contents)
		class _Model(cls, Model): pass
		
		table.bind(_Model)

		return _Model
	return model_inner

####

@model('users', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text', CheckConstraint(lambda x: x < 10)),
	'organization_id': Column('fk:organizations.id')
})
class User: pass

@model('countries', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text'),
	'misc_data': Column('json'),
	'planet_id': Column('fk:planets.id')
})
class Country: pass

@model('organizations', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text'),
	'country_id': Column('fk:countries.id')
})
class Organization: pass

@model('planets', {
	'id': Column('serial', PrimaryKeyConstraint()),
	'name': Column('text')
})
class Planet: pass


for t in _tables: #TODO nononononono
	for c in t.columns:
		c.type.late_bind(c)

for t in order_tables():
	exec_statement(CreateStatement(t))


#j = planets.join(users.join(orgs).join(countries))
j = User.join(Organization, Organization.name == 'My Org.').join(Country)

exec_statement(SelectStatement(j))

c = Country()
c.__loaded__(True)
c.misc_data