#	coding utf-8
'''
Unit tests on model ORM
'''

from . import *

TEST_TABLE = 'canvas_unit_test'

#	TODO: Fuckin cleeean

@test('ORM')
def test_orm():
	from ..exceptions import ValidationErrors
	#	Also testing importability
	from .. import model

	session = model.create_session()
	
	def drop_table():
		try:
			session.execute(f'DROP TABLE {TEST_TABLE};')
			session.conn.commit()
		except:
			session.rollback()
	drop_table()

	case('Basic functionality')
	j, k = ([], []) # Callback trackers

	@model.schema(TEST_TABLE, {
		'a': model.Column('uuid', primary_key=True),
		'b': model.Column('text')
	})
	class X:
		
		def __init__(self, b):
			self.b = b

		def __on_create__(self):
			k.append('called')

		def __on_load__(self):
			j.append('called')

	model.create_tables()

	check((
		len(session.query(X)) == 0
	), 'Empty query')

	x = X('Hello!')
	session.save(x)
	session.commit()
	
	session = model.create_session()
	all_x = session.query(X)
	check((
		len(all_x) == 1 and
		all_x[0].a == x.a and
		all_x[0].b == x.b
	), 'Reconstruction works for non-empty * query')
	
	check((
		'called' in j and
		'called' in k
	), 'Creation and reconstruction callbacks invoked')

	y = session.query(X, X.a == x.a, one=True)
	check((
		y is not None and
		y.b == x.b
	), 'Matching simple single query')

	all_y = session.query(X, X.a == 'foobar')
	check((
		len(all_y) == 0
	), 'Non-matching simple query returns empty list')

	y = session.query(X, X.a == 'foobar', one=True)
	check((
		y is None
	), 'Non-matching simple single query returns None')

	session = model.create_session()

	new_pk = 'a'*32
	x = session.query(X, one=True)
	x.a = new_pk
	session.commit()

	session = model.create_session()

	y = session.query(X, X.a == new_pk, one=True)
	check((
		y is not None and
		y.b == x.b and
		y.a == x.a
	), 'Primary key updates flushed to disk')
	#	TODO: Prevent double activation!
	
	case('Constraints, accessors, and complex columns')
	drop_table()
	session = model.create_session()

	@model.schema(TEST_TABLE, {
		'a': model.Column('serial', primary_key=True),
		'b': model.Column('text', unique=False, constraints=[
			model.RegexConstraint('my_constraint', 'Something happened', '^\w{5,}$')
		]),
		'c': model.Column('json', unique=False, nullable=True)
	}, accessors=['a'])
	class Y:
		
		def __init__(self, b, c=None):
			self.b, self.c = (b, c)
		
	model.create_tables()

	x = Y('foobar')
	session.save(x)
	x_ser = x.a

	check((
		x_ser == 1
	), 'SQL defaults mapped on save()')

	session.commit()

	session = model.create_session()
	x = Y.get(session, x_ser)

	check((
		x is not None and
		x.a == x_ser and
		x.b == 'foobar'
	), 'get() class method')

	session = model.create_session()
	y = Y('foo')
	
	def save_y():
		session.save(y)
		session.commit()

	check_throw(save_y, ValidationErrors, 'Regex validation in precheck')
	session.rollback()

	y = Y('foobar')
	save_y()
	y_ser = y.a

	both = session.query(Y, Y.b == 'foobar')
	check((
		len(both) == 2 and
		both[0].a == x_ser and
		both[1].a == y_ser
	), 'Two item matching query')
	x = both[0]
	
	y.b = 'foobar2'
	session.commit()
	
	session.delete(y)
	session.commit()
	check((
		len(session.query(Y, Y.b == 'foobar2')) == 0
	), 'Deletion')

	y = Y.get(session, x.a)
	check((
		y is x
	), 'Class accessor get yields already-mapped model')

	session.delete(y)
	session.commit()
	all_y = session.query(Y)
	check((
		len(all_y) == 0
	), 'Multiple-reference deletion')

	y = Y('foobar', [1, 2, 3])
	session.save(y)
	session.commit()

	session = model.create_session()
	y = session.query(Y, Y.b == 'foobar', one=True)
	print(y.c)

