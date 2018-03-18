#	coding utf-8
'''
Command-line invocation.
'''

import sys
sys.path.insert(0, '.')

import canvas
canvas.launch(*sys.argv[1:])
