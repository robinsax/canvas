#	coding utf-8
'''
Unit tests on the canvas utilities package.
'''

import sys

from . import *

utils_test = TestSuite('utils')

@utils_test('registration')
def test_registration():
	from ..utils.registration import (
		register,
		get_registered,
		get_registered_by_name,
		place_registered_on
	)

	@register('test')
	def test1(): pass

	@register.test
	def test2(): pass

	l = get_registered('test')
	check((
		len(l) == 2 and 
		l[0] == test1 and 
		l[1] == test2
	), 'List retrieval')

	m = get_registered_by_name('test')
	check((
		len(m) == 2 and 
		m.get('test1', None) == test1 and 
		m.get('test2', None) == test2
	), 'By-name dict retrieval')

	here = sys.modules[__name__]
	place_registered_on(__name__, 'test')
	check((
		getattr(here, 'test1', None) == test1,
		getattr(here, 'test2', None) == test2
	), 'Placement')

@utils_test('WrappedDict')
def test_wrapped_dict():
	from ..utils import WrappedDict

	class TestKeyError(Exception):
		pass

	w = WrappedDict({
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
