#	codidng utf-8
'''
Top-level statement objects.
'''

class Statement:
	'''The top-level AST node type, which must facilitate value collection.'''

	def write(self):
		'''Return an SQL, value list tuple of this statement's serialization'''
		raise NotImplementedError()

class CreateStatement(Statement):
	'''A lazy SQL CREATE statement.'''

	def __init__(self, target):
		self.target = deproxy(target)

	def write(self):
		return ' '.join((
			'CREATE', self.target.object_type, 'IF NOT EXISTS',
				self.target.describe()
		)), tuple()

class SelectStatement(Statement):
	'''An SQL SELECT statement.'''

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

class UpdateStatement(Statement): pass
