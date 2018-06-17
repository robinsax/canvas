#	coding utf-8
'''
Callback registration and invocation.
'''

from .namespace import export, export_ext

#	The global map.
_callbacks = dict()

def _register(func, type_name):
	#	Ensure list exists.
	if type_name not in _callbacks:
		_callbacks[type_name] = []
	
	#	Register.
	_callbacks[type_name].append(func)

@export_ext
def define_callback_type(type_name, arguments=tuple(), ext=False):
	#	TODO: Argspec inspector.

	def psuedo(func):
		_register(func, type_name)
		return func

	def psuedo_invoke(*args, **kwargs):
		invoke_callbacks(type_name, *args, **kwargs)
	psuedo.invoke = psuedo_invoke

	export_fn = export_ext if ext else export
	export_fn('on_%s'%type_name)(psuedo)

	return psuedo

@export_ext
def invoke_callbacks(type_name, *args, **kwargs):
	if type_name not in _callbacks:
		return
	
	for callback in _callbacks[type_name]:
		callback(*args, **kwargs)