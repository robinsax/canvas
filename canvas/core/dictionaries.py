#	coding utf-8
'''
Special dictionary definitions.
'''

from ..exceptions import UnprocessableEntity

class AttributedDict(dict):

	def __init__(self, content=dict()):
		for key, value in content.items():
			self[key] = value
	
	def __getattr__(self, attr):
		return self[attr]

	def __setitem__(self, attr, value):
		if type(value) == dict:
			value = self.__class__(value)
		super().__setitem__(attr, value)
	
	def __setattr__(self, attr, value):
		self[attr] = value

class RequestParameters(AttributedDict):

	def __getitem__(self, item):
		if item not in self:
			raise UnprocessableEntity('Missing request parameter {}'.format(item))
		return super().__getitem__(item)

class Configuration(AttributedDict):

	def __init__(self, content=dict()):
		for key, value in content.items():
			self[key] = value

	def __setitem__(self, key, value):
		if isinstance(value, dict):
			value = Configuration(value)
		super().__setitem__(key, value)