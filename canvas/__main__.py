import os
import sys

sys.path.insert(0, '.')

def usage():
	print('Usage: python3.6 canvas [ --serve PORT | --run_tests ]')
	sys.exit(1)

if len(sys.argv) < 2:
	usage()

mode = sys.argv[1][2:]
if mode == 'serve':
	try:
		port = int(sys.argv[2])
	except:
		usage()

	from werkzeug.serving import run_simple
	from canvas import application

	run_simple('localhost', port, application)
elif mode == 'run_tests':
	from canvas import tests

	sys.exit(tests.run())
else:
	usage()
