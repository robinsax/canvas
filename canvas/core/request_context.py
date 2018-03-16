#	coding utf-8
'''
The request context object definition.
'''

from threading import Lock, get_ident

from ..namespace import export
from .dictionaries import AttributedDict

_request_contexts = {}
_lock = Lock()

@export
class RequestContext(AttributedDict):

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

	def __getitem__(self, item):
		if isinstance(item, int):
			return (self['request'], self['cookie'], self['session'])[:item]
		return super().__getitem__(item)