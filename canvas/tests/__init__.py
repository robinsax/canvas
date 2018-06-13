# coding: utf-8
'''
The testing API defined in this package is for authoring unit test suites
against either canvas itself of plugins. It's corresponding CLI launch
argument is `--test`.
'''

from ..exceptions import Failed
from ..utils import logger, format_exception

#	Create a log.
log = logger(__name__)

#	Define the global test function list.
_tests = list()

def test(name):
	'''The test function registrar.'''
	def inner_test(func):
		func.__test__ = name
		_tests.append(func)
		return func
	return inner_test

class assertion:
	'''A context within which assertions can be safely performed.'''
	this_test = 0

	def __init__(self, name, ex_cls=None):
		self.name = name
		self.ex_cls = ex_cls

	def __enter__(self):
		log.info('\t%s', self.name)

	def do_passed(self):
		log.info('\t\tPassed')
		assertion.this_test += 1

	def __exit__(self, ex_type, ex_value, traceback):
		if self.ex_cls:
			if not traceback or not isinstance(ex_value, self.ex_cls):
				log.warning('\t\tFailed')
				raise Failed()
			else:
				self.do_passed()
				return True
		else:
			if traceback and isinstance(ex_value, AssertionError):
				log.warning('\t\tFailed')
				log.warning(format_exception(ex_value))
				raise Failed()
			else:
				self.do_passed()

def run_tests():
	passed, failed = 0, 0
	log.info('Running %d tests', len(_tests))

	for test in _tests:
		assertion.this_test = 0
		log.info('Running test: %s', test.__test__)

		try:
			test()
			log.info('\tPassed! (%d assertions)', assertion.this_test)
			passed += 1
		except Failed as ex:
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
