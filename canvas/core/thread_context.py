#	coding utf-8
'''
Request context to thread ID mapping.
'''

from threading import Lock, get_ident

__all__ = [
	'get_thread_context',
	'register_thread_context',
	'remove_thread_context'
]

#	The request context to thread ID mapping.
_thread_contexts = {}

#	Although performed operations are atomic in CPython, that behaviour isn't
#	guarenteed, so the small locking overhead is prefered for stability.
_thread_contexts_lock = Lock()

def register_thread_context(ctx):
	'''
	Maps `ctx` to the current thread.
	'''
	_thread_contexts_lock.acquire()
	_thread_contexts[get_ident()] = ctx
	_thread_contexts_lock.release()

def get_thread_context():
	'''
	Retrieve the request context mapped to the current thread, or `None` if 
	there isn't one.
	'''
	_thread_contexts_lock.acquire()
	try:
		ctx = _thread_contexts[get_ident()]
	except KeyError:
		ctx = None
	_thread_contexts_lock.release()

	return ctx

def remove_thread_context():
	'''
	Remove the request context mapped to the current thread.
	'''
	_thread_contexts_lock.acquire()
	try:
		del _thread_contexts[get_ident()]
	except KeyError: pass
	_thread_contexts_lock.release()
