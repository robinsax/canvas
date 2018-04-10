#	coding utf-8
'''
Special dictionary definitions.
'''

from ..exceptions import UnprocessableEntity
from ..namespace import export_ext

@export_ext
class AttributedDict(dict):

	def __init__(self, content=dict()):
		for key, value in content.items():
			self[key] = value
	
	def __getattr__(self, attr):
		return self[attr]

	def __setitem__(self, attr, value):
		propagate = getattr(self.__class__, '__propagate__', True)
		if propagate and type(value) == dict:
			value = self.__class__(value)
		super().__setitem__(attr, value)
	
	def __setattr__(self, attr, value):
		self[attr] = value

@export_ext
class LazyAttributedDict(AttributedDict):
	__propagate__ = False

@export_ext
class RequestParameters(AttributedDict):

	def __getitem__(self, item):
		if item not in self:
			raise UnprocessableEntity('Missing request parameter %s'%item)
		return super().__getitem__(item)

@export_ext
class Configuration(AttributedDict):

	def __init__(self, content=dict()):
		for key, value in content.items():
			self[key] = value

	def __setitem__(self, key, value):
		if isinstance(value, dict):
			value = Configuration(value)
		super().__setitem__(key, value)
