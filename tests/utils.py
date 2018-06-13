# coding: utf-8
'''
Tests on the `utils` and `dictionaries` packages.
'''

from datetime import datetime

import canvas.tests as cvt

from canvas.exceptions import Immutable, BadRequest
from canvas.utils import create_callback_registrar, cached_property
from canvas.dictionaries import RequestParameters
from canvas.json_io import serialize_datetime

@cvt.test('Utilities')
def test_utilities():
	with cvt.assertion('Unlooped callback registration'):
		registrar = create_callback_registrar()
		x = list()

		registrar(lambda: x.append(1))
		registrar.invoke()

		assert len(x) == 1
	
	with cvt.assertion('Looped callback registration'):
		registrar = create_callback_registrar(loop_arg=True)
		registrar(lambda x: x + 1)

		assert registrar.invoke(0) == 1

	with cvt.assertion('Cached properties'):
		y = [False]
		class X:
			@cached_property
			def f(self):
				y[0] = not y[0]

		x = X(); x.f; x.f
		assert y[0]

@cvt.test('RequestParameters dictionary')
def test_dictionaries():
	#	Prepare an instance.
	input_dict = {
		'x': [
			{
				'y': {
					'z': 1
				}
			}
		]
	}
	rp = RequestParameters(input_dict)
	rp.allowed_key = 1
	rp.datetime = serialize_datetime(datetime.now())
	rp.propagate_and_lock()

	#	Perform assertions.
	with cvt.assertion('Lock applies', Immutable):
		rp.new_key = 2
	with cvt.assertion('Missing parameter applies', BadRequest):
		rp.fake_key
	with cvt.assertion('Type check applies', BadRequest):
		rp[('allowed_key', datetime)]
	with cvt.assertion('Datetime type check applies'):
		rp[('datetime', datetime)]
