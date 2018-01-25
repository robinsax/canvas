#	coding utf-8
'''
Unit tests on controller and component objects.
'''

import canvas as cv

from canvas import controllers

from . import *

controller_test = TestSuite('canvas.controllers')

@controller_test('Controllers')
def test_controllers():
	'''
	Unit tests on controller objects.
	'''

	#	Define test controllers.
	@cv.register.controller
	class TestEndpoint(controllers.APIEndpoint):

		def __init__(self):
			super().__init__('/api/test')

	@cv.register.controller
	class TestPage(controllers.Page):

		def __init__(self):
			super().__init__('/test', 'Test', **{
				'dependencies': ['fake.txt']
			})

	controllers.create_everything()

	#	Test package-level instance access functions.
	case('Controller instance access functions')

	classes = [inst.__class__ for inst in controllers.get_controllers()]
	check((
		TestEndpoint in classes and
		TestPage in classes
	), 'Get controllers returns complete list')

	inst = controllers.get_controller('/api/test') 
	check((
		inst is not None and
		inst.__class__ is TestEndpoint
	), 'Controller retrieval by route')

	check_throw((
		lambda: inst.get({})
	), cv.UnsupportedMethod, '`405` on invalid method')

	inst = controllers.get_controller('/test')
	check((
		inst is not None and
		inst.__class__ is TestPage
	), 'Controller retrieval corrects route')

	check((
		'fake.txt' in inst.collect_dependencies()[0]
	), 'Dependency collection')

	check_throw((
		lambda: inst.get({})
	), cv.TemplateNotFound, 'Page tries to render')

@controller_test('Components')
def test_components():
	'''
	Unit tests on components. Relies on the preceding test.
	'''
	
	@cv.register.component
	class TestComponent(controllers.Component):

		def __init__(self):
			super().__init__('test_component', [
				'/api/test'
			])

		def check(self, ctx):
			if 'no' in ctx:
				raise cv.Unavailable()

	controllers.create_everything()

	controller = controllers.get_controller('/api/test')
	components = controller.get_components({})
	check((
		len(components) == 1 and
		components[0].__class__ is TestComponent
	), 'Get component retrieval: component accepts')

	check((
		len(controller.get_components({'no': True})) == 0
	), 'Get component retrieval: component rejects')