# coding: utf-8
'''
A set of special dictionaries used throughout canvas.
'''

from datetime import datetime

from .exceptions import Immutable, ValidationErrors

class AttributedDict(dict, object):
	'''
	A dictionary that allows item access and assignment through attributes.
	'''

	def __init__(self, content=dict(), ignored=tuple(), **kwargs):
		'''
		Create a new attribute-bound dictionary.
		::contents A source dictionary.
		::kwargs Additional dictionary items.
		'''
		self.__ignored__ = ignored
		for key, value in content.items():
			self[key] = value
		for key, value in kwargs.items():
			self[key] = value
	
	def __getattr__(self, attr):
		if attr == '__ignored__' or attr in self.__ignored__:
			return super().__getattribute__(attr)
		return self[attr]
	
	def __setattr__(self, attr, value):
		if attr == '__ignored__' or attr in self.__ignored__:
			return super().__setattr__(attr, value)
		self[attr] = value

#	TODO: Review the need for immutability.
class RequestParameters(AttributedDict):
	'''
	The dictionary used to contain supplied request parameters which allows
	an appropriate response to be implicitly dispatched when a required 
	parameter is not supplied by the client. Request parameters are immutable
	at controller dispatch time.

	To assert the type of a required parameter on retrieval pass a key, type
	tuple as the key. For example:
	```
	input_num = request[('number', int)]
	```
	'''

	def __init__(self, content, locked=False):
		super().__init__(content, ignored=('_locked', 'propagate_and_lock'))
		self._locked = locked

	@classmethod
	def propagate_onto(cls, current_object):
		'''
		Replace all dictionaries within `current_object` with 
		`RequestParameters`.
		'''
		if isinstance(current_object, dict):
			for key, value in current_object.items():
				if isinstance(value, dict):
					current_object[key] = cls(value)
				cls.propagate_onto(current_object[key])
		elif isinstance(current_object, (list, tuple)):
			for i, item in enumerate(current_object):
				if isinstance(item, dict):
					current_object[i] = cls(item)
					cls.propagate_onto(current_object[i])

	def propagate_and_lock(self):
		'''Propagate this dictionary type onto all constituent dictionaries.'''
		RequestParameters.propagate_onto(self)
		self._locked = True

	def get(self, key, default):
		if key in self:
			return self[(key, type(default))]
		return default

	def __setitem__(self, key, value):
		try:
			locked = self._locked
		except AttributeError:
			locked = False
		if locked:
			raise Immutable()
		return super().__setitem__(key, value)

	def __getitem__(self, key):
		#	Maybe unpack the key as a tuple with a type expectation.
		expected_typ = None
		if isinstance(key, (list, tuple)):
			key, expected_typ = key
		
		if key not in self:
			#	This required parameter was not supplied.
			raise ValidationErrors({key: 'Missing'})
		
		value = super().__getitem__(key)
		if not expected_typ:
			#	No need to assert.
			return value
		
		if expected_typ is datetime:
			from .core import parse_datetime
			#	Distrustfully parse.
			return parse_datetime(value)
		elif expected_typ is bool and isinstance(value, str):
			if value == 'true':
				return True
			elif value == 'false':
				return False
		elif isinstance(value, expected_typ):
			#	Passed.
			return value
		
		#	Failed.
		raise ValidationErrors({key: 'Expected %s'%expected_typ.__name__})
		
class Configuration(AttributedDict):
	'''
	The configuration dictionary, which propagates to constituent dictionaries.
	'''

	def __setitem__(self, key, value):
		if isinstance(value, dict):
			value = Configuration(value)
		super().__setitem__(key, value)
