import os, socket
#import threading, weakref

class LeginonObject(object):
	def __init__(self, id):
		self.id = id
		self.idcounter = 0

	def location(self):
		'return a dict describing the location of this object'
		loc = {}
		loc['hostname'] = socket.gethostname()
		loc['PID'] = os.getpid()
		loc['python ID'] = id(self)
		#loc['thread'] = threading.currentThread()
		#loc['weakref'] = weakref.ref(self)
		return loc

	def print_location(self):
		loc = self.location()
		print '     Leginon Object: %s' % (self.id,)
		for key,value in loc.items():
			print '         %-25s  %s' % (key,value)

	def ID(self):
		newid = self.id + (self.idcounter,)
		self.idcounter += 1
		return newid
