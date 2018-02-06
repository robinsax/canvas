#   coding utf-8
'''
Unit tests on thread context storage.
'''

import canvas as cv

from threading import Thread, Barrier

from canvas.tests import *

THREAD_COUNT = 20

thread_storage_test = TestSuite('canvas.core.thread_context')

@thread_storage_test('Per-thread storage')
def test_thread_storage():
	'''
	Unit tests on thread aware context storage.
	'''

	passed, crash = True, None
	#	Use a barrier so concurrent execution is not a race condition.
	barrier = Barrier(THREAD_COUNT)

	def do_test(k):
		'''
		The test executed by each thread.
		'''
		barrier.wait()
		try:
			ctx = {'number': k}
			cv.register_thread_context(ctx)

			check((
				get_thread_context() == ctx
			), f'Thread {k}: context equality')

			cv.remove_thread_context()

			check((
				cv.get_thread_context() == None
			), f'Thread {k}: empty context returns None')
		except Fail:
			#	No concurrent readers => this is safe.
			passed = False
		except BaseException as e:
			#	Same as above.
			crash = e
    
	threads = []
	for i in range(THREAD_COUNT):
		thread = Thread(target=do_test, args=(i,))
		thread.start()
		threads.append(thread)

	for thread in threads:
		thread.join()
	
	if crash is not None:
		raise crash

	if not passed:
		fail()
