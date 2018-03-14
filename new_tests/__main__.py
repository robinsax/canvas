import new_canvas as cv

@cv.init
def my_init_callback():
	print('Init. callback!')

@cv.controller('/route')
class Ayetroller:
	
	def do_get(self, ctx):
		return 'Aye!'

cv.initialize()

print(cv.core._route_map)

cv.serve()