
import os, socket

class LeginonObject(object):
	def __init__(self):
		self.loc = {}
		self.loc['hostname'] = socket.gethostname()
		self.loc['pid'] = os.getpid()
		self.loc['pythonid'] = id(self)
		self.id = self.get_id()

	def location(self):
		'return a dict describing the location of this object'
		return self.loc

	def get_id(self):
		return id(self)

	def future_get_id(self):
		## this is unique, but not if persistent objects come and go
		loc = self.location()
		myid = (loc['hostname'], loc['pythonid'])
		return myid
