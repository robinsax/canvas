# coding: utf-8
'''
The entry point of canvas's CLI.
'''

#	Ensure canvas is importable.
import sys
sys.path.insert(0, '.')

#	Import and invoke the launch handler.
from canvas import launch_cli
launch_cli((str(),) if len(sys.argv) == 1 else sys.argv[1:])
