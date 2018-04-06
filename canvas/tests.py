#	coding utf-8
'''
Testing interface definition.
'''

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from .utils import logger, format_exception

log = logger(__name__)

_tests = []

class Failure(Exception): pass

def fail(message):
	raise Failure(message)

def test(name):
	def test_wrap(func):
		func.__test__ = name
		_tests.append(func)
		return func
	return test_wrap

def assertion(name, condition):
	log.info('\t%s', name)
	if not condition:
		raise Failure('Failed assertion %s'%name)

def raise_assertion(name, cls, trigger):
	log.info('\t%s', name)
	try:
		trigger()
	except cls:
		return
	raise Failure('Failed raise assertion: %s'%name)

def create_client():
	from . import application
	return Client(application, BaseResponse)

def run_tests():
	from .core import initialize_controllers
	initialize_controllers()
	
	passed, failed = 0, 0
	log.info('Running %d tests', len(_tests))

	for test in _tests:
		log.info('Running test: %s', test.__test__)

		try:
			test()
			passed += 1
		except Failure as ex:
			log.warning('\tFailed!\n%s', format_exception(ex))
			failed += 1
		except BaseException as ex:
			log.critical('\tCrashed!\n%s', format_exception(ex))
			failed += 1
		
	log.info('Passed %s / Failed %s', passed, failed)
	if failed == 0:
		log.info('---- Passing ----')
		return True
	else:
		log.info('---- Failing ----')
		return False
