#	coding utf-8
'''
Command-line invocation.
'''

import sys
sys.path.insert(0, '.')

from canvas import launch
launch([''] if len(sys.argv) == 1 else sys.argv[1:])
