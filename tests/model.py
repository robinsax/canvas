#	coding utf-8
'''
Models and serialization.
'''

import canvas as cv
import canvas.tests as cvt

@cvt.test('Basic Model operations')
def test_model_basic():
	@cv.model('test_models', {
		'id': cv.Column('serial', primary_key=True),
		'text': cv.Column('text', (
			cv.NotNullConstraint(),
		))
	})
	class TestObject: pass

	cvt.reset_model()
	session = cv.create_session()

	obj = TestObject()
	obj.text = 'foobar'

	session.save(obj).commit().reset()

	cvt.assertion(
		'Save and load occur',
		TestObject.get(obj.id, session).text == 'foobar'
	)

	invalid_obj = TestObject()

	cvt.raise_assertion(
		'Contraints applied',
		cv.ValidationErrors,
		lambda: session.save(invalid_obj)
	)