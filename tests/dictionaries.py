#	coding utf-8
'''
Tests on special dictionaries.
'''

import canvas as cv

from canvas.core.dictionaries import (
	Configuration,
	RequestParameters
)

@cv.test('Configuration object')
def test_configuration():
	configuration = Configuration({
		'key1': 1,
		'key2': {
			'sub1': 2,
			'sub2': 3
		}
	})

	cv.assertion(
		'Copy and __getitem__ correct',
		configuration.key1 == 1
	)

	cv.assertion(
		'Propagation occurrs', 
		configuration.key2.sub1 == 2
	)

@cv.test('RequestParameters object')
def test_request_parameters():
	request_parameters = RequestParameters({
		'key1': 1
	})

	cv.assertion(
		'Copy occurs',
		request_parameters['key1']
	)

	cv.raise_assertion(
		'UnprocessableEntity occurs', 
		cv.UnprocessableEntity,
		lambda: request_parameters['key2']
	)
