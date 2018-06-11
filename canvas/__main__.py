# coding: utf-8
'''
canvas's command line invocation entry point.
'''

#	Ensure canvas is importable.
import sys
sys.path.insert(0, '.')

#	Import and invoke the launch handler.
from canvas import launch
launch((str(),) if len(sys.argv) == 1 else sys.argv[1:])
