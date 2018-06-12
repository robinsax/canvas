# coding: utf-8
'''
The CLI API definition, available to both the core and plugins.
'''

import sys

#	Define the global name to launcher function map.
_launchers = dict()
#	Define a single character to launcher function map.
_shortforms = dict()

def launcher(name, **info):
	'''
	Register a launcher function to be referenced from the CLI as `name`. An
	abbreviation will be automatically assigned if one is available. The `info`
	keyword arguments can contain one or more of:
	* `description` - A textual description of the launch mode.
	* `argspec` - A CLI argument specification.
	* `init` - A flag indicating a full initialization is required before the
		handler is invoked.
	'''
	def launcher_wrap(func):
		ref_name, char = name, name[0]
		func.__info__ = info
		
		if char not in _shortforms:
			#	Assign a short form alias.
			ref_name = ''.join(('(', char, ')', name[1:]))
			_shortforms[char] = func
		
		info['ref_name'] = ref_name
		_launchers[name] = func
		return func
	return launcher_wrap

def launch_cli(args):
	'''Launch the CLI given the commandline arguments `args`.'''
	#	Define the incorrect usage handler.
	def print_usage():
		#	Define the argument representation generatior.
		def write_one(name, launcher):
			ref_name = launcher.__info__['ref_name']
			string = ' '.join(
				(''.join(('--', ref_name)), launcher.__info__.get('argspec', ''))
			)
			string = ''.join((
				string, ' '*(35 - len(string)), 
				launcher.__info__.get('description', '')
			))
			return string
		
		#	Sort launch options alphabetically.
		alpha_order = sorted(_launchers.keys())
		print(' '.join((
			'Usage:',
			'python3 canvas [',
				'\n\t' + '\n\t'.join(
					write_one(name, _launchers[name]) for name in alpha_order
				),
			'\n]'
		)))
		
		#	Exit.
		sys.exit(1)
	
	if args and args[0] == '-!':
		#	The -i switch causes eager initialization.
		from ..core import initialize
		initialize()

		args = args[1:]
	
	#	Nothing supplied, show usage.
	if not args:
		print_usage()

	#	Look up the launcher.
	launcher = None
	if args[0].startswith('--'):
		launcher = _launchers.get(args[0][2:])
	elif args[0].startswith('-'):
		launcher = _shortforms.get(args[0][1:])
	if not launcher:
		print_usage()
	
	if launcher.__info__.get('init', False):
		#	This launcher requires initialization.
		from ..core import initialize
		initialize()

	if launcher(args[1:]) is False:
		#	The launch function reported incorrect usage.
		print_usage()
