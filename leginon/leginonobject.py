
import os, socket

class LeginonObject(object):
	def __init__(self):
		self.loc = {}
		self.loc['hostname'] = socket.gethostname()
		self.loc['pid'] = os.getpid()
		self.loc['pythonid'] = id(self)

	def location(self):
		'return a dict describing the location of this object'
		return self.loc

