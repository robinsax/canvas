import canvas as cv

from canvas import controllers

@cv.register('controller')
class LandingPage(controllers.Page):

	def __init__(self):
		super().__init__('/', 'Welcome', template='landing')
