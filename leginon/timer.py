import time

class Timer(object):
	def __init__(self, message=''):
		self.message = message
#		print 'Timer Start: %s' % (self.message,)
		self.t0 = time.time()

	def stop(self):
		t1 = time.time()
		tdiff = t1 - self.t0
#		print 'Timer Stop: %s, Time: %.2f' % (self.message, tdiff)
