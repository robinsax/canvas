#	coding utf-8
'''
Combined tests for good request handler coverage.
'''

import canvas as cv

from canvas.tests import *

MISSING_PATH = '/api/nowhere'
ENDPOINT_PATH = '/api/test'

combined_test = TestSuite('canvas')

@combined_test('Basic controllers and request handling')
def test_basic():
	'''
	Basic tests on controllers and the request handler using API endpoints.
	'''
	import canvas as cv
	
	from canvas import controllers

	#	Define a basic endpoint.
	@cv.register.controller
	class TestEndpoint(controllers.APIEndpoint):

		def __init__(self):
			super().__init__(ENDPOINT_PATH)
		
		def get(self, ctx):
			return cv.create_json('success')

		def post(self, ctx):
			request = ctx['request']
			return cv.create_json('success', {
				'sent': request['item']
			})

	#	Re-initialize controllers.
	controllers.create_everything()
	#	Create a psuedo-client.
	client = create_client()

	check_json_response(
		client.get(MISSING_PATH), 
		404,
		lambda j: j['status'] == 'error',
		'Non-present endpoint GET'
	)

	check_json_response(
		client.get(ENDPOINT_PATH), 
		200,
		lambda j: j['status'] == 'success',
		'Present endpoint GET'
	)

	check_json_response(
		client.post(ENDPOINT_PATH),
		400,
		lambda j: (
			j['status'] == 'error' and 
			j['data']['code'] == 400 and
			j['data']['description'] == 'Missing Request Parameter: item'
		),
		'Missing request parameter handling'
	)

	check((
		client.get('/assets/base.css').status_code == 200
	), 'base.css serves')

	check((
		client.get('/assets/core.min.js').status_code == 200
	), 'core.min.js serves')

	check_html_response(client.get('/'), 200, 
			lambda html: 'Hello World!' in html, 'Hello world page serves')
