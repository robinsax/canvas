# coding: utf-8
'''
The request context object definition.
'''

from threading import Lock, get_ident

from ..namespace import export_ext
from .dictionaries import LazyAttributedDict

_request_contexts = {}
_lock = Lock()

class RouteString(str):

	def set_variables(self, variables):
		for k, v in variables.items():
			setattr(self, k, v)

@export_ext
class RequestContext(LazyAttributedDict):

	@classmethod
	def get(cls):
		ident = get_ident()
		with _lock:
			current = _request_contexts.get(ident)
		return current
	
	@classmethod
	def put(cls, instance):
		ident = get_ident()
		with _lock:
			_request_contexts[ident] = instance

	@classmethod
	def pop(cls):
		ident = get_ident()
		with _lock:
			current = _request_contexts.pop(ident)
		return current

	def __init__(self, source):
		super().__init__(source)
		self.indexed = ['request', 'cookie', 'session', 'route']

	def __getitem__(self, item):
		if isinstance(item, (int, slice)):
			return [self[k] for k in self.indexed][item]
		return super().__getitem__(item)
