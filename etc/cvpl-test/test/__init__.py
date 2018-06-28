# coding: utf-8
'''
The test plugin for canvas.
'''

import uuid
import random
import canvas as cv

from .words import words as _words

words = _words.split('\n')

@cv.endpoint('/api/trash')
class TrashEndpoint:

	def create_trash(self):
		def make_text():
			text = str()
			for i in range(random.randint(3, 7)):
				text += ' ' + words[random.randint(0, len(words) - 1)]
			return text

		return {
			'id': uuid.uuid4(),
			'number': random.randint(1, 10),
			'text': make_text(),
			'kids': list(make_text() for i in range(random.randint(0, 3)))
		}
	

	def on_get(self, context):
		cnt = context.query.get('count', 10)

		trash = []
		for i in range(random.randint(1, cnt)):
			trash.append(self.create_trash())\

		return cv.create_json('success', trash)

@cv.page('/test', title='Test', assets=('test.js',))
class TestPage: pass
