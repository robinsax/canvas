#	coding utf-8
'''
Used to store the request context per-thread.
Although this is only used internally now, it
could be exposed to plugins later.
'''

from threading import Lock, get_ident

__all__ = [
	'register_thread_context',
	'get_thread_context',
	'remove_thread_context'
]

#	TODO: Upgrade concurrency management
#	to a readers-writers soln

#	The dictionary for storing the
#	request context for each thread,
#	and its lock
_thread_contexts = {}
_thread_contexts_lock = Lock()

def register_thread_context(ctx):
	'''
	Adds `ctx` as the per-thread request
	context for the current thread
	'''
	_thread_contexts_lock.acquire()
	_thread_contexts[get_ident()] = ctx
	_thread_contexts_lock.release()

def get_thread_context():
	'''
	Retrieve the per-thread request context
	for the current thread
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
	Remove the per-thread request context
	for the current thread
	'''
	_thread_contexts_lock.acquire()
	try:
		del _thread_contexts[get_ident()]
	except KeyError: pass
	_thread_contexts_lock.release()
