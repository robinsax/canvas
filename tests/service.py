# coding: pyxl
'''
Full service testing.
'''

import canvas.tests as cvt

from canvas.json_io import serialize_json, deserialize_json
from canvas.core.controllers import endpoint, page
from canvas.core.model import dictize
from canvas.core.views import view
from canvas.core.responses import create_json

from .controller_service import reload_controllers
from .model import test_models

#    Create a test client.
client = cvt.create_client()

@cvt.test('Full service')
def test_full_service():
    Country, Company, Employee, Flag = test_models

    #    Create some controllers.
    should_crash = False
    @endpoint('/api/country_data')
    class CountryEndpoint:

        def on_get(self, context):
            if should_crash:
                raise Exception()
            
            country = context.query.country
            data = context.session.query(
                Country.join(
                    Company.join(Employee, attr='employees'), attr='companies'
                ).add(Flag, attr='flag'),
                Country.name == country
            )

            return create_json('success', dictize(data, include=('employees', 'companies', 'flag')))

    reload_controllers()

    with cvt.assertion('Error responses'):
        assert client.get('/fake-route').status_code == 404
        assert client.get('/api/country_data').status_code == 400

        should_crash = True
        assert client.get('/api/country_data').status_code == 500
        should_crash = False

    with cvt.assertion('Correct responses'):
        correct_get = client.get('/api/country_data', 
            content_type='application/json',
            query_string='country=United States of Trump'
        )
        usa = deserialize_json(correct_get.data)['data'][0]
        assert usa['abbreviation'] == 'U.S.T.'
        assert usa['flag']['name'] == 'Stars and Stripes'
