#	coding utf-8
'''
Unit tests on canvas
'''

import sys
import logging

__all__ = [
	'test',
	'case',
	'check',
	'check_throw',
	'Fail'
]

log = logging.getLogger(__name__)

def case(desc):
	log.debug(f'\t | - {desc}')

class Fail(Exception):
	pass

_tests = []
def test(name, on_fail=None):
	def wrap(fn):
		_tests.append((name, fn, on_fail))
		return fn
	return wrap

def check(cond, message='Generic check'):
	log.debug(f'\t\t| - {message}')
	if not cond:
		raise Fail(message)

def check_throw(trigger, ex_cls, message='Generic throw check'):
	log.debug(f'\t\t| - Throw {ex_cls.__name__}: {message}')
	try:
		trigger()
	except ex_cls: return
	raise Fail(message)

from . import utils, templates, orm

def run():
	passed_cnt = 0
	failed_names = []
	for name, test_fn, fail_fn in _tests:
		log.info(f'-- Running tests against {name} --')
		try:
			test_fn()
			passed_cnt += 1
			log.info('\t--> Passed')
		except Fail as fail:
			if fail_fn is not None:
				fail_fn()
			failed_names.append(name)
			tb = fail.__traceback__.tb_next
			log.warning(f'\t--> Failed! ({str(fail)}; {tb.tb_frame.f_code.co_filename}, line {tb.tb_lineno})')
	failed_cnt = len(failed_names)
	if failed_cnt == 0:
		log.info(f'Done, build passing ({passed_cnt} passed)')
		return 0
	else:
		log.critical(f'Done, build failing ({passed_cnt} passed, {failed_cnt} failed)')
		log.info('Failed tests:')
		for name in failed_names:
			log.info(f'\t{name}')
		return 1