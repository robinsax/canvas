# coding: utf-8
'''
The CLI API definition, available to both the core and plugins.
'''

#	Define the global name to launcher function map.
_launchers = dict()

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
		func.__info__ = info
		_launchers[name] = func
		return func
	return launcher_wrap

def launch_cli(args):
	'''Launch the CLI given the commandline arguments `args`.'''
	def print_usage():
		def create_string(name, launcher):
			first = '%s %s'%(name, launcher.__info__.get('argspec', ''))
			first = '%s%s%s'%(first, ' '*(35 - len(first)), launcher.__info__.get('description', ''))
			return first
		
		print(' '.join([
			'Usage:',
			'python3 canvas [',
				'\n\t' + '\n\t'.join([
					create_string(name, _launchers[name]) for name in sorted(_launchers.keys())
				]),
			'\n]'
		]))
		sys.exit(1)

	def get_launcher(item):
		launcher_match = re.match(r'--(.*)', args[k])
		if launcher_match is None:
			return None
		return launcher_match.group(1) 

	
	if '-i' in args:
		from ..core import initialize
		initialize()

		args.remove('-i')
	
	if len(args) == 0:
		print_usage()

	k = 0
	launcher = None
	while k < len(args):
		launcher = get_launcher(args[k])
		if launcher is None or launcher not in _launchers:
			print_usage()
		k += 1

		args_here = []
		while k < len(args) and get_launcher(args[k]) is None:
			args_here.append(args[k])
			k += 1

		launcher = _launchers[launcher]

		if launcher.__info__.get('init', False):
			from ..core import initialize
			initialize()

		if not launcher(args_here):
			print_usage()
