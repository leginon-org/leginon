
import os, socket

class LeginonObject(object):
	def __init__(self):
		pass

	def location(self):
		'return a dict describing the location of this object'
		loc = {}
		loc['hostname'] = socket.gethostname()
                loc['pid'] = os.getpid()
		loc['pythonid'] = id(self)
		return loc
