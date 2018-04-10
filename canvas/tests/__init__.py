#	coding utf-8
'''
Testing interface definition.
'''

from ..utils import logger, format_exception

log = logger(__name__)

_tests = []
_assertions = [0]

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

	_assertions[0] += 1

def raise_assertion(name, cls, trigger):
	log.info('\t%s', name)
	try:
		trigger()
	except cls:
		_assertions[0] += 1
		return
	
	raise Failure('Failed raise assertion: %s'%name)

def create_client():	
	from .client import CanvasTestClient
	
	return CanvasTestClient()

def reset_controllers():
	from ..core import initialize_controllers

	initialize_controllers()

def reset_model():
	from ..core.model import initialize_model

	initialize_model()

def run_tests():
	passed, failed = 0, 0
	log.info('Running %d tests', len(_tests))

	for test in _tests:
		_assertions[0] = 0
		log.info('Running test: %s', test.__test__)

		try:
			test()
			log.info('\tPassed! (%d assertions)'%_assertions[0])
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
