#	coding utf-8
'''
Unit tests on the canvas model package.
'''

import canvas as cv

from canvas import model
from canvas.tests import *

model_test = TestSuite('canvas.model')

#	A table name to use for the contained unit tests.
TEST_TABLE = '__canvas_unit__'
TEST_TABLE_2 = '__canvas_unit_2__'
TEST_TABLE_3 = '__canvas_unit_3__'

def reset(session):
	'''
	Drop the test table if it exists.
	'''
	drops = [
		f'DROP TABLE {TEST_TABLE_3};',
		f'DROP TABLE {TEST_TABLE_2};',
		f'DROP TABLE {TEST_TABLE};'
	]
	for drop in drops:
		try:
			session.execute(drop)
			session.commit()
		except:
			session.rollback()

	model._wipe()

@model_test('Basic functionality')
def basics():
	session = model.create_session()
	reset(session)

	#	Create callback trackers.
	load_called, create_called = [False], [False]

	#	Create test model.
	@model.schema(TEST_TABLE, {
		'a': model.Column('uuid', primary_key=True),
		'b': model.Column('text')
	})
	class X:
		
		def __init__(self, b):
			self.b = b

		def __on_create__(self):
			create_called[0] = True

		def __on_load__(self):
			load_called[0] = True

	#	Issue the creation SQL.
	model.create_everything()

	check((
		len(session.query(X)) == 0
	), 'Empty query')

	#	Create an instance.
	x = X('Hello!')
	session.save(x)
	session.commit()
	
	#	Retrieve instance with new session.
	session = model.create_session()
	all_x = session.query(X)
	check((
		len(all_x) == 1 and
		all_x[0].a == x.a and
		all_x[0].b == x.b
	), 'Reconstruction works for non-empty * query')
	
	check((
		True in load_called and
		True in create_called
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

#	TODO: Rats nest.
@model_test('Constraints, accessors, and complex columns')
def test_orm():
	session = model.create_session()
	reset(session)
	
	#	Create test table.
	@model.schema(TEST_TABLE, {
		'a': model.Column('serial', primary_key=True),
		'b': model.Column('text', constraints=[
			model.RegexConstraint('Something happened', '^\w{5,}$')
		]),
		'c': model.Column('json', default=lambda: {'foo': 'bar'})
	}, accessors=['a'])
	class Y:
		
		def __init__(self, b):
			self.b = b
		
	model.create_everything()

	x = Y('foobar')
	session.save(x)
	x_ser = x.a

	check((
		x_ser == 1
	), 'SQL defaults mapped on save()')

	check((
		x.c.get('foo', None) == 'bar'
	), 'Complex defaults mapped on save()')

	session.commit()

	session = model.create_session()
	x = Y.get(x_ser, session)

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

	check_throw(save_y, cv.ValidationErrors, 'Regex validation in precheck')
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
	
	session.delete(y).commit()
	check((
		len(session.query(Y, Y.b == 'foobar2')) == 0
	), 'Deletion')

	y = Y.get(x.a, session)
	check((
		y is x
	), 'Class accessor get yields already-mapped model')

	session.delete(y).commit()
	all_y = session.query(Y)
	check((
		len(all_y) == 0
	), 'Multiple-reference deletion')

@model_test('Foreign keys')
def test_table_creation_order():
	session = model.create_session()
	reset(session)

	subcase('Declaration')

	@model.schema(TEST_TABLE_3, {
		'id': model.Column('serial', primary_key=True),
		'pointer': model.Column(f'fk:{TEST_TABLE_2}.id'),
		'pointer2': model.Column(f'fk:{TEST_TABLE}.id')
	})
	class X: pass

	@model.schema(TEST_TABLE_2, {
		'id': model.Column('serial', primary_key=True),
		'pointer': model.Column(f'fk:{TEST_TABLE}.id')
	})
	class Y: pass

	@model.schema(TEST_TABLE, {
		'id': model.Column('serial', primary_key=True)
	})
	class Z: pass

	subcase('Table ordering and creation')
	try:
		model.create_everything()
	except cv.InvalidSchema:
		fail('Order not resolved')

@model_test('Non-model queries')
def non_model_queries():
	session = model.create_session()
	reset(session)

	#	Set up.
	@model.schema(TEST_TABLE, {
		'id': model.Column('serial', primary_key=True),
		'text': model.Column('text')
	})
	class X:
		
		def __init__(self, text):
			self.text = text

	model.create_everything()

	#	Save instances.
	session.save(X('aaaa'))
	for i in range(5):
		session.save(X('hello'))
	session.save(X('hi')).commit()

	#	Test.
	check((
		session.query(X.id.count()) == 7
	), 'Unconditioned count aggregator')

	check((
		session.query(X.id.count(), X.text == 'hello') == 5
	), 'Conditioned count aggregator')

	check((
		session.query(min(X.text)) == 'aaaa'
	), 'Unconditioned min aggregator')
