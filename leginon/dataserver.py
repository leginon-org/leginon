import leginonobject
import clientpush
import clientpull

class DataServer(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.pushserver = clientpush.Server()
		self.pullserver = clientpull.Server()

