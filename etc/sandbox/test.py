#	Here's what I want.

import canvas as cv

@cv.model('table', {
	'column': cv.Column('int')
})
class N:
	pass

@cv.endpoint('/endpoint-route')
class Z(cv.Endpoint()):
	pass

@cv.page('/page-route')
class X:
	pass

@cv.routing
def setup_my_routes(routes):
	routes['/page-route-2'] = '/page-route'



#################3

define_callback_type('init')