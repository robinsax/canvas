# coding: utf-8
'''
A set of special dictionaries used throughout canvas.
'''

from datetime import datetime

from .exceptions import Immutable, UnprocessableEntity, BadRequest

class AttributedDict(dict):
	'''
	A dictionary that allows item access and assignment through attributes.
	'''

	def __init__(self, content=dict(), **kwargs):
		'''
		Create a new attribute-bound dictionary.
		::contents A source dictionary.
		::kwargs Additional dictionary items.
		'''
		for key, value in content.items():
			self[key] = value
		for key, value in kwargs:
			self[key] = value
	
	def __getattr__(self, attr):
		return self[attr]
	
	def __setattr__(self, attr, value):
		self[attr] = value

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
		super().__init__(content)
		self.locked = locked

	@classmethod
	def propagate_onto(cls, current_object):
		'''
		Replace all dictionaries within `current_object` with 
		`RequestParameters`.
		'''
		if isinstance(current_object, dict):
			for key, value in current_object.items():
				if isinstance(value, dict):
					current_object[key] = cls(value, True)
					cls.propagate_onto(visit_one(current_object[key]))
				else:
					visit_one(value)
		elif isinstance(current_object, (list, tuple)):
			for i, item in enumerate(current_object):
				if isinstance(item, dict):
					current_object[i] = cls(item, True)
					cls.propagate_onto(current_object[i])

	def propagate_and_lock(self):
		'''Propagate this dictionary type onto all constituent dictionaries.'''
		RequestParameters.propagate_onto(self)
		self.locked = True

	def __setitem__(self, key, value):
		if self.locked:
			raise Immutable()
		return super().__setitem__(key, value)
		
	def __getitem__(self, key):
		#	Maybe unpack the key as a tuple with a type expectation.
		expected_typ = None
		if isinstance(key, (list, tuple)):
			key, expected_typ = key
		
		if key not in self:
			#	This required parameter was not supplied.
			raise UnprocessableEntity('Missing request parameter "%s"'%key)
		
		value = super().__getitem__(key)
		if not expected_typ:
			#	No need to assert.
			return value
		
		if expected_typ is datetime:
			from .core import parse_datetime
			#	Distrustfully parse.
			return parse_datetime(value)
		elif isinstance(value, expected_typ):
			#	Passed.
			return value
		
		#	Failed.
		raise BadRequest('Invalid request parameter type for "%s"'%key)

class Configuration(AttributedDict):
	'''
	The configuration dictionary, which propagates to constituent dictionaries.
	'''

	def __setitem__(self, key, value):
		if isinstance(value, dict):
			value = Configuration(value)
		super().__setitem__(key, value)
