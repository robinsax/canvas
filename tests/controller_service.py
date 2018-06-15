# coding: utf-8
'''
Unit tests on the controller and routing modules.
'''

import canvas.tests as cvt

from canvas.core.controllers import controller, page, endpoint, \
	create_controllers
from canvas.core.routing import create_routing, resolve_route

@cvt.test('Controllers and routing')
def test_controllers_and_routing():
	#	Create some test controllers.
	@controller('/a/<x>')
	class BasicController: pass
	@endpoint('/api/<y>/c/<z>')
	class EndpointController: pass
	@page('/p', title='Test Page')
	class PageController: pass

	#	Reinitialize the routing module.
	create_routing(create_controllers())

	with cvt.assertion('Route variables resolve correctly'):
		instance, route_vars = resolve_route('/a/1')
		assert isinstance(instance, BasicController) and \
				route_vars['x'] == '1'
		
		instance, route_vars = resolve_route('/api/3/c/2')
		assert isinstance(instance, EndpointController) and \
				route_vars['y'] == '3' and route_vars['z'] == '2'

	with cvt.assertion('Page variables populated from decorator'):
		html = resolve_route('/p')[0].render()[0]
		assert '<title>Test Page</title>' in html
