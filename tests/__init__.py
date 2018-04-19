#	coding utf-8
'''
Unit tests on the canvas backend.
'''

import canvas.tests as cvt

from . import (
	dictionaries
)

@cvt.test('Basic asset service')
def test_asset_service():
	client = cvt.create_client()

	response = client.get('/assets/canvas.js')
	cvt.assertion(
		'canvas.js serves',
		response.status_code == 200
	)

	response = client.get('/')
	cvt.assertion(
		'Welcome serves',
		response.status_code == 200
	)

