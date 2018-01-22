#	coding utf-8
'''
Request-context is mapped to thread id to allow
a cleaner interface for certain methods.
'''

from threading import Lock, get_ident

__all__ = [
	'get_thread_context',
	'register_thread_context',
	'remove_thread_context'
]

#	The dictionary for mapping the request
#	context for each thread.
_thread_contexts = {}

#	Although setting, deleting, and retrieving 
#	items is atomic in CPython, it isn't part of 
#	specification. Additionally, the introduced 
#	locking overhead is minimal
_thread_contexts_lock = Lock()

def register_thread_context(ctx):
	'''
	Adds `ctx` as the per-thread request context 
	for the current thread.
	'''
	_thread_contexts_lock.acquire()
	_thread_contexts[get_ident()] = ctx
	_thread_contexts_lock.release()

def get_thread_context():
	'''
	Retrieve the per-thread request context for 
	the current thread, or `None` if there
	isn't one.
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
	Remove the per-thread request context for 
	the current thread.
	'''
	_thread_contexts_lock.acquire()
	try:
		del _thread_contexts[get_ident()]
	except KeyError: pass
	_thread_contexts_lock.release()
