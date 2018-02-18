#	coding utf-8
'''
Unit tests on miscellaneous stuff.
'''

import canvas as cv

from canvas.utils.doc_builder import build_docs

from canvas.tests import *

misc_test = TestSuite('canvas(misc)')

@misc_test
def test_build_doc():
	try:
		build_docs(cv)
	except:
		fail()
