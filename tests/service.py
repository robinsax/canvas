# coding: utf-8
'''
Service tests.
'''

import canvas.tests as cvt

@cvt.test('Basic service')
def test_asset_service():
	client = cvt.create_client()

	response = client.get('/assets/canvas.js')
	cvt.assertion(
		'canvas.js serves',
		response.status_code == 200
	)

	response = client.get('/assets/canvas.css')
	cvt.assertion(
		'canvas.css serves',
		response.status_code == 200
	)

	response = client.get('/')
	cvt.assertion(
		'Welcome serves',
		response.status_code == 200
	)

	response = client.get('/not-found')
	cvt.assertion(
		'404 serves as page',
		response.status_code == 404 and 'text/html' in response.headers['Content-Type']
	)

	response = client.get_json('/api/not-found')
	cvt.assertion(
		'API 404 serves as JSON',
		response.status_code == 404 and response.json['status'] == 'error'
	)

