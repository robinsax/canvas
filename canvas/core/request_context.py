# coding: utf-8
'''
The request context object definition. Request contexts are extensible objects
containing everything required to handle a response including the request 
parameters and the database as well as cookie sessions. When created, request
contexts are linked to the current thread. The current request context can be
accessed at any time with `RequestContext.get`.
'''

from threading import Lock, get_ident

from ..dictionaries import AttributedDict

class RequestContext(AttributedDict):
	'''
	The request context class definition. Instances of this object support
	slicing and indexing; when a slice or index access is encountered, the
	values for the keys in the corresponding portion of the `indexed`
	attribute are returned.
	'''
	#	Define the thread-safe thread to request context map.
	instance_map = dict()
	instance_map_lock = Lock()

	@classmethod
	def get(cls):
		'''
		Retrieve the request context associated with the current thread, or 
		`None`.
		'''
		with cls.instance_map_lock:
			current = cls.instance_map.get(get_ident())
		return current
	
	@classmethod
	def put(cls, context):
		'''Associated `context` with the current thread.'''
		with cls.instance_map_lock:
			cls.instance_map[get_ident()] = context

	@classmethod
	def pop(cls):
		'''
		De-associate and return the request context associated with the current
		thread.
		'''
		ident = get_ident()
		with cls.instance_map_lock:
			current = cls.instance_map.pop(get_ident())
		return current

	def __init__(self, **kwargs):
		'''Create a new request context.'''
		super().__init__(**kwargs)
		if self.verb == 'get':
			self.indexed = ['query', 'session', 'route', 'cookie']
		else:
			self.indexed = ['request', 'session', 'route', 'cookie']

	def __getitem__(self, item):
		'''Retrieve an item, allowing slicing and indexing.'''
		if isinstance(item, (int, slice)):
			return [self[k] for k in self.indexed][item]
		return super().__getitem__(item)
