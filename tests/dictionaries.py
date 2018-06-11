# coding: utf-8
'''
Tests on special dictionaries.
'''

import canvas.tests as cvt

from canvas.exceptions import UnprocessableEntity
from canvas.core.dictionaries import (
	Configuration,
	RequestParameters
)

@cvt.test('Configuration object')
def test_configuration():
	configuration = Configuration({
		'key1': 1,
		'key2': {
			'sub1': 2,
			'sub2': 3
		}
	})

	cvt.assertion(
		'Copy and __getitem__ correct',
		configuration.key1 == 1
	)

	cvt.assertion(
		'Propagation occurrs', 
		configuration.key2.sub1 == 2
	)

@cvt.test('RequestParameters object')
def test_request_parameters():
	request_parameters = RequestParameters({
		'key1': 1
	})

	cvt.assertion(
		'Copy occurs',
		request_parameters['key1']
	)

	cvt.raise_assertion(
		'UnprocessableEntity occurs', 
		UnprocessableEntity,
		lambda: request_parameters['key2']
	)
