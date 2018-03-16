import logging
import sys

logging.basicConfig(level=logging.DEBUG, handlers=[
	logging.StreamHandler(sys.stdout)
])

import canvas as cv

@cv.model('mytable', {
	'pasta': cv.Column('uuid', primary_key=True),
	'boi': cv.Column('text')
})
class PastaBoi:

	def __init__(self, boi):
		self.boi = boi

@cv.on_init
def init_callback():
	print('I happmd!')

@cv.controller('/')
class Ctrl:

	def on_get(self, context):
		if 'name' in context.request:
			context.cookie['name'] = context.request.name
			print(context.cookie.should_save)
		if 'name' in context.cookie:
			return 'Hello %s'%context.cookie['name']
		return 'Hello %s'%context.request.name

@cv.page('/page', template='test.html')
class Cnfl:

	def on_get(self, context):
		return self.render()

cv.serve()