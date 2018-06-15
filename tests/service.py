# coding: utf-8
'''
Full service testing.
'''

import canvas.tests as cvt

from canvas.json_io import serialize_json, deserialize_json
from canvas.core.controllers import endpoint, page
from canvas.core.model import dictize
from canvas.core.responses import create_json

from .controller_service import reload_controllers
from .model import test_models

#	Create a test client.
client = cvt.create_client()

@cvt.test('Full service')
def test_full_service():
	Country, Company, Employee, Flag = test_models

	#	Create some controllers.
	should_crash = False
	@endpoint('/api/country_data')
	class CountryEndpoint:

		def on_get(self, context):
			if should_crash:
				raise Exception()
			
			country = context.query.country
			data = context.session.query(
				Country.join(
					Company.join(Employee, attr='employees')
				).add(Flag, attr='flag'),
				Country.name == country
			)

			return create_json('success', dictize(data, include=('employees', 'flag')))

	reload_controllers()

	with cvt.assertion('Error responses'):
		empty_get = client.get('/fake-route')
		assert empty_get.status_code == 404

		missing_param_get = client.get('/api/country_data')
		assert missing_param_get.status_code == 400

	with cvt.assertion('Correct responses'):
		correct_get = client.get('/api/country_data', 
			content_type='application/json',
			query_string='country=United States of Trump'
		)
		response_data = deserialize_json(correct_get.data)
		print(response_data)
		assert response_data['data'][0]['abbreviation'] == 'U.S.T.'
