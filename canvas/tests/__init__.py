#	coding utf-8
'''
Unit tests on canvas.

Provides an interface for plugin tests.
'''

import sys
import imp
import uuid

from werkzeug.wrappers import BaseResponse
from werkzeug.test import Client

from ..utils import logger
from ..core.plugins import get_path_occurrences
from .. import application

#	TODO: Refactor.

__all__ = [
	'TestSuite',
	'Fail',
	'fail',
	'create_client',
	'case',
	'subcase',
	'check',
	'check_throw',
	'check_json_response',
	'check_html_response'
]

#	Create a testing logger.
log = logger('tests')

#	The test suite master list.
_suites = []
class TestSuite:
	'''
	A test suite registration decorator.
	'''

	def __init__(self, name):
		'''
		Create a decorator for registering a new test 
		suite called `name`.
		'''
		self.name, self.tests = name, []

		#	Add this suite to the master list.
		_suites.append(self)

	def __call__(self, test_name, on_fail=None):
		def wrap(fn):
			self.tests.append((test_name, fn, on_fail))
			return fn
		return wrap

class Fail(Exception):
	'''
	Raised to fail a test. Any other exception being 
	propogated will cause the test to be considered broken.
	'''
	pass

def fail(desc='Generic failure'):
	'''
	Fail a test.
	'''
	raise Fail(desc)

def create_client():
	'''
	Create and return a werkzeug testing client.
	'''
	return Client(application, BaseResponse)

def case(desc):
	'''
	Log the current case being tested.
	'''
	log.debug(f'\t | - {desc}')

def subcase(desc):
	'''
	Log the current subcase being tested.
	'''
	log.debug(f'\t\t| - {desc}')

def check(cond, message='Generic check'):
	'''
	Perform a check, failing the build if it fails.
	'''
	subcase(message)

	if not cond:
		raise Fail(message)

def check_throw(trigger, ex_cls, message='Generic throw check'):
	'''
	Perform a check for a thrown exception, failing
	the build if it fails.
	'''
	log.debug(f'\t\t| - Throw {ex_cls.__name__}: {message}')

	try:
		trigger()
	except ex_cls: return
	raise Fail(message)

def check_json_response(response, status, json_valid, name):
	'''
	Perform a check on a JSON response produced by a testing
	client.
	'''
	check((
		response.status_code == status and
		json_valid(json.loads(response.data))
	), name)

def check_html_response(response, status, html_valid, name):
	'''
	Perform a check on a JSON response produced by a testing
	client.
	'''
	check((
		response.status_code == status and
		html_valid(response.data)
	), name)

#	Allow sub-modules to create test suites.
from . import (
	utils,
	thread_contexts,
	assets,
	model,
	controllers,
	combined
)

def run_tests(suites):
	'''
	Run all registered tests, returning `True` if
	the build is passing and `False` otherwise.
	'''
	#	Import plugin tests packages to allow them to
	#	create suites. A UUID is used as the import name 
	#	since all packages are named `test` and are never
	#	referenced by name.
	for test_pkg_path in get_path_occurrences('tests/', include_base=False):
		imp.load_source(uuid.uuid4().hex, f'{test_pkg_path}/__init__.py')
	#	Do the same for modules.
	for test_module_path in get_path_occurrences('tests.py', include_base=False):
		imp.load_source(uuid.uuid4().hex, test_module_path)

	run_all = len(suites) == 0

	#	Initialize pass/fail tracking.
	passed_cnt, failed_names = 0, []
	
	#	Iterate suites.
	for suite in _suites:
		#	Check if this suite should be skipped.
		if not run_all and suite.name not in suites:
			continue
		
		log.info(f'---- Running test suite: {suite.name} ----')

		#	Iterate tests.
		for name, test_fn, fail_fn in suite.tests:
			log.info(f'-- Running test: {name} --')

			try:
				test_fn()
				passed_cnt += 1
				log.info('\t--> Passed')
			except Fail as fail:
				if fail_fn is not None:
					#	Allow the test to clean up resources it
					#	was using.
					fail_fn()
				#	Track the failure.
				failed_names.append(f'{suite.name}: {name}')

				#	Record failure specifics.
				tb = fail.__traceback__.tb_next
				log.warning(f'\t--> Failed! ({str(fail)}; {tb.tb_frame.f_code.co_filename}, line {tb.tb_lineno})')
	
	#	Count failed.
	failed_cnt = len(failed_names)
	if failed_cnt == 0:
		#	Build passing.
		log.info(f'Done, build passing ({passed_cnt} passed)')
		return True
	else:
		#	Build failing.
		log.critical(f'Done, build failing ({passed_cnt} passed, {failed_cnt} failed)')
		#	Log failed tests.
		log.info('Failed tests:')
		for name in failed_names:
			log.info(f'\t{name}')
		return False
