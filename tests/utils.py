# coding: utf-8
'''
Tests on the `utils` and `dictionaries` packages.
'''

import canvas.tests as cvt

from canvas.utils import create_callback_registrar, cached_property
from canvas.dictionaries import RequestParameters

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
	input_dict = {
		'x': [
			{
				'y': {
					'z': 1
				}
			}
		]
	}
	
	with cvt.assertion('2 stage creation', True):
		rp = RequestParameters(input_dict)
		rp.propagate_and_lock()
	
	