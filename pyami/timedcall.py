#!/usr/bin/env python
'''
This module implements a way to call a function that may run indefinitely
when you do not want to block the caller indefinitely.  Just wrap your
function call in the provided "call" function.  If your function returns
within the specified timeout period, then you will get the return value
as usual.  If your function raises and exception, or it does not return
within the specified timeout period, then an exception will be raised.

For instance, you have a
function that runs for 10 seconds:

	def myfunc():
		time.sleep(10)

Now you want to call it, but you only give it 5 seconds to return:

	import timedcall
	timedcall.call(myfunc, timeout=5)

After 5 seconds, an exception will be raised because myfunc ran too long.
Note: myfunc still runs in another thread for the remaining 5 seconds as
long as python is still running, but we abandon it and can never get its
return value.

If we had given myfunc longer to run, for instance 20 seconds:

	timedcall.call(myfunc, timeout=20)

This would return immediately after myfunc returns, and we could get an
actual return value instead of an exception being raised.
'''

import threading
import time
import sys

class ThreadWithReturnValue(threading.Thread):
	'''A thread that remembers the target function's return value or exception'''
	def run(self):
		try:
			self.returnvalue = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
			self.exception = None
		except:
			self.returnvalue = None
			self.exception = sys.exc_info()

def call(func, timeout=None, *args, **kwargs):
	'''Call a function, but only wait 'timeout' seconds for it to return'''
	if timeout is None:
		# no timeout specified means call as usual, blocking until return
		return func(*args, **kwargs)
	else:
		# run function in another thread, wait for it to return, or give up
		# after specified timeout
		t = ThreadWithReturnValue(target=func, args=args, kwargs=kwargs)
		t.setDaemon(True)
		t.start()
		t.join(timeout)
		if not t.isAlive():
			## either returned or raised exception
			if t.exception is not None:
				raise t.exception[0], t.exception[1], t.exception[2]
			else:
				return t.returnvalue
		else:
			raise RuntimeError('%s timed out after %.2f seconds' % (func.__name__, timeout))

#### Tests ########
if __name__ == '__main__':
	def test_function(t=0):
		print 'This function returns after %.2f seconds' % (t,)
		time.sleep(t)
		return 'DONE'

	import sys
	ftime = 0
	if len(sys.argv) > 1:
		ftime = float(sys.argv[1])
	ret = call(test_function, timeout=2, t=ftime)
	print 'RET', ret
