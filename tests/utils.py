#	coding utf-8
'''
Unit tests on the canvas utilities package.
'''

import sys
import json
import datetime as dt

import canvas as cv

from canvas.tests import *

utils_test = TestSuite('canvas.utils')

@utils_test('Registration')
def test_registration():
	'''
	Unit tests on the registration utility.
	'''

	@cv.register('test')
	def test1(): pass

	@cv.register.test
	def test2(): pass

	#	Test list retrieval.
	l = cv.get_registered('test')
	check((
		len(l) == 2 and 
		l[0] == test1 and 
		l[1] == test2
	), 'List retrieval')

	#	Test map retrieval.
	m = cv.get_registered_by_name('test')
	check((
		len(m) == 2 and 
		m.get('test1', None) == test1 and 
		m.get('test2', None) == test2
	), 'By-name dict retrieval')

	#	Test placement.
	here = sys.modules[__name__]
	cv.place_registered_on(__name__, 'test')
	check((
		getattr(here, 'test1', None) == test1,
		getattr(here, 'test2', None) == test2
	), 'Placement')

	#	Test clearing.
	cv.clear_registered('test')
	check((
		len(cv.get_registered('test')) == 0
	), 'Clearing')

@utils_test('WrappedDict')
def test_wrapped_dict():
	'''
	Unit tests on the WrappedDict object.
	'''

	class TestKeyError(Exception):
		pass

	w = cv.WrappedDict({
		'a': 1,
		'b': 2,
		'c': 3
	}, TestKeyError)

	check((
		w['a'] == 1,
		w['b'] == 2,
		w['c'] == 3
	), '__getitem__() retrieval')
	check((
		w.get('a', 4) == 1,
		w.get('d', 4) == 4
	), 'get()')
	check_throw(lambda: w['d'], TestKeyError, 'Custom exception')

@utils_test('Traceback formatting')
def test_traceback_format():
	'''
	Unit test on `format_traceback()` to ensure it returns output.
	'''
	#	Generate an exception.
	try:
		raise Exception()
	except Exception as e:
		ex = e
	
	#	Format it.
	try:
		cv.format_traceback(ex)
	except:
		fail()

@utils_test('JSON serialization and de-serialization')
def test_json():
	benchmark = dt.datetime.now()

	inputs = {
		'foo': 100,
		'bar': 'foobar',
		'bench': benchmark
	}

	subcase('Serialization')
	try:
		serialized = cv.serialize_json(inputs)
	except BaseException:
		fail()
	
	subcase('Deserialization')
	try:
		deserialized = cv.deserialize_json(serialized)
	except BaseException:
		fail()
	
	check((
		isinstance(benchmark, dt.datetime) and
		deserialized['bench'].minute == benchmark.minute and 
		deserialized['bench'].second == benchmark.second
	), 'Identity translation on round-trip')
