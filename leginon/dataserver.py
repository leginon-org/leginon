import leginonobject
import clientpush
import clientpull

class DataServer(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		# perhaps better done in child class
		#self.pushserver = clientpush.Server()
		#self.pullserver = clientpull.Server()
		self.pushserver = None
		self.pullserver = None

