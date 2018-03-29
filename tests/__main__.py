#	coding utf-8
'''
tmp as fuck launch point
'''

import logging
import sys

logging.basicConfig(level=logging.DEBUG, handlers=[
	logging.StreamHandler(sys.stdout)
])
sys.path.insert(0, '.')

import new_tests
