# coding: utf-8
'''
Unit tests against the exceptions module.
'''

import canvas.tests as cvt

from canvas.exceptions import HTTPException, ValidationErrors

@cvt.test('HTTPExceptions')
def test_http_exceptions():
	ex = HTTPException(100, 'Test', 'Description')
	with cvt.assertion('Simple response tuples'):
		simple_response = ex.simple_response()
		assert (
			simple_response[0] == 'Test' and 
			simple_response[1] == 100 and 
			simple_response[3] == 'text/plain'
		)

	ex = ValidationErrors({'x': 'y'}, 'z')
	with cvt.assertion('Error dict constitution'):
		error_dict = ex.get_info()
		assert (
			'code' in error_dict and
			'title' in error_dict and
			'errors' in error_dict and
			'error_summary' in error_dict
		)
