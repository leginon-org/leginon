#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import time

class Timer(object):
	def __init__(self, message=''):
		self.message = message
		print 'Timer Start: %s' % (self.message,)
		self.t0 = time.time()

	def stop(self):
		t1 = time.time()
		tdiff = t1 - self.t0
		print 'Timer Stop: %s, Time: %.2f' % (self.message, tdiff)

	def reset(self):
		print 'Timer Start: %s' % (self.message,)
		self.stop()
		self.t0 = time.time()

