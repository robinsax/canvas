#	coding utf-8
'''
Simple combine tests for good request handler coverage.
'''

import json

from werkzeug.wrappers import BaseResponse
from werkzeug.test import Client

from . import *

MISSING_PATH = '/api/nowhere'
ENDPOINT_PATH = '/api/test'

combine_test = TestSuite('canvas')

@combine_test('Basic controllers and request handling')
def test_basic():
	'''
	Basic tests on controllers and the request handler using API endpoints.
	'''
	from ..utils.registration import register
	from ..core import create_json
	from ..controllers import APIEndpoint, create_everything
	from .. import application

	def check_json_response(response, status, json_valid, name):
		check((
			response.status_code == status and
			json_valid(json.loads(response.data))
		), name)

	#	Define a basic endpoint.
	@register.controller
	class TestEndpoint(APIEndpoint):

		def __init__(self):
			super().__init__(ENDPOINT_PATH)
		
		def get(self, ctx):
			return create_json('success')

		def post(self, ctx):
			request = ctx['request']
			return create_json('success', {
				'sent': request['item']
			})

	#	Re-initialize controllers.
	create_everything()
	#	Create a psuedo-client.
	client = Client(application, BaseResponse)

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
		client.get('/assets/style.css').status_code == 200
	), 'style.css serves')
