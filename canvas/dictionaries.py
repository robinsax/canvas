#	coding utf-8
'''
A set of special dictionaries used throughout canvas.
'''

from .exceptions import UnprocessableEntity

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
	parameter is not supplied by the client.
	'''

	def __getitem__(self, key):
		if key not in self:
			#	This required parameter was not supplied.
			raise UnprocessableEntity('Missing request parameter "%s"'%key)
		return super().__getitem__(key)

class Configuration(AttributedDict):
	'''
	The configuration dictionary, which propagates to constituent dictionaries.
	'''

	def __setitem__(self, key, value):
		if isinstance(value, dict):
			value = Configuration(value)
		super().__setitem__(key, value)
