#	coding utf-8
'''
The registration utility, used throughout canvas
'''

import sys

__all__ = [
	'register',
	'get_registered',
	'get_registered_by_name',
	'call_registered',
	'place_registered_on'
]

_registrations = {}
def register(*types):
	'''
	A registration decorator for classes and
	functions to allow canvas to identify plugin-generated
	classes and functions.
	:types The one or more types to register the class
		or function as
	'''
	def wrap(obj):
		for type in types:
			if type not in _registrations:
				_registrations[type] = []
			_registrations[type].append(obj)
		return obj
	return wrap

def get_registered(*types):
	'''
	Return all registered classes or functions of `type`, 
	or an empty list if there are none.
	'''
	l = []
	for type in types:
		l.extend(_registrations.get(type, []))
	return l

def call_registered(type, *args, **kwargs):
	to_call = get_registered(type)
	for func in to_call:
		func(*args, **kwargs)

def get_registered_by_name(type):
	'''
	Return a dictionary containing all classes or
	functions of `type`, mapped by name.
	'''
	as_dict = {}
	for item in get_registered(type):
		as_dict[item.__name__] = item
	return as_dict

def place_registered_on(name, type):
	'''
	Add all registered classes or functions
	of the given type to a module's namespace.
	:name The name of the module to add to
	:type The type to add registered objects of
	'''
	module = sys.modules[name]
	if getattr(module, '__all__', None) is None:
		module.__all__ = []
	for item in get_registered(type):
		module.__all__.append(item.__name__)
		setattr(module, item.__name__, item)
