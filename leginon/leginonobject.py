import os, socket
#import threading, weakref

class LeginonObject(object):
	def __init__(self):
		self.id = id(self)

	def location(self):
		'return a dict describing the location of this object'
		loc = {}
		loc['hostname'] = socket.gethostname()
		loc['PID'] = os.getpid()
		loc['python ID'] = id(self)
		#loc['thread'] = threading.currentThread()
		#loc['weakref'] = weakref.ref(self)
		return loc

