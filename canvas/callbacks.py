#	coding utf-8
'''
Callback registration and invocation.
'''

from .namespace import export

#	The global map.
_callbacks = dict()

def _register(func, type_name):
	#	Ensure list exists.
	if type_name not in _callbacks:
		_callbacks[type_name] = []
	
	#	Register.
	_callbacks[type_name].append(func)

def define_callback_type(type_name, arguments):
	#	TODO: Allow argspec inspector.

	def psuedo(func):
		_register(func, type_name)
		return func
	
	export('on_%s'%type_name)(psuedo)
	return type_name

def invoke_callbacks(type_name, *args, **kwargs):
	if type_name not in _callbacks:
		return
	
	for callback in _callbacks[type_name]:
		callback(*args, **kwargs)