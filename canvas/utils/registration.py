#	coding utf-8
'''
A utility that allows arbitrary functions and classes to be identified and
managed via decorator.
'''

import sys

#	Declare dependencies.
__all__ = [
	#	Registration.
	'register',
	'callback',
	#	De-registration.
	'clear_registered',
	#	Registration access.
	'get_registered',
	'get_registered_by_name',
	'call_registered',
	'place_registered_on'
]

#	The registration list mapping.
_registrations = {}

class _RegistrationDecoratorGenerator:
	'''
	A decorator generator that enables registration by string parameter, or 
	by attribute access for reduced syntax.
	'''

	def __init__(self, prefix=''):
		'''
		Create a registration decorator generator.

		:prefix A prefix to automatically add to all registered types.
		'''
		self.prefix = prefix

	def __call__(self, *types):
		#	Define the decorator.
		def wrap(obj):
			for typ in types:
				#	Add prefix.
				typ = f'{self.prefix}{typ}'

				#	Ensure list presence.
				if typ not in _registrations:
					#	Initialize as empty.
					_registrations[typ] = []

				#	Add.
				_registrations[typ].append(obj)
			return obj

		#	Return decorator.
		return wrap

	def __getattr__(self, typ):
		def psuedo(cls):
			return self(typ)(cls)
		
		return psuedo

#	Create the two implementations.
register = _RegistrationDecoratorGenerator()
callback = _RegistrationDecoratorGenerator('callback:')

#	Remove the reference.
del _RegistrationDecoratorGenerator

def get_registered(*types):
	'''
	Return all registered classes or functions registered as the given types 
	or an empty list if there are none.
	'''
	lst = []
	for typ in types:
		lst.extend(_registrations.get(typ, []))

	return lst

def get_registered_by_name(*types):
	'''
	Generate and return a dictionary containing all classes or functions 
	registered as the given type, keyed by name.
	'''
	dct = {}
	for typ in types:
		dct.update({o.__name__: o for o in get_registered(typ)})

	return dct

def call_registered(typ, *args, **kwargs):
	'''
	Invoke all functions registered as `typ`. The callback prefix is 
	prepended if not present.
	'''
	if not typ.startswith('callback:'):
		#	Add prefix.
		typ = f'callback:{typ}'
	
	for func in get_registered(typ):
		func(*args, **kwargs)

def clear_registered(typ):
	'''
	Remove all registrations for `typ` if there are any.
	'''
	if typ in _registrations:
		del _registrations[typ]

def place_registered_on(name, typ):
	'''
	Add all registered classes or functions of the given typ to a module or 
	package namespace.

	:name The name of the module whose namespace is the target.
	:typ The registered type to place.
	'''
	#	Retrieve the module.
	module = sys.modules[name]

	#	Ensure `__all__` list existance
	if getattr(module, '__all__', None) is None:
		module.__all__ = []
	
	#	Place all registered.
	for item in get_registered(typ):
		module.__all__.append(item.__name__)
		setattr(module, item.__name__, item)
