
import leginonobject, outserver, outclient

class OutHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.outclient = outclient.OutClient()
		self.outserver = outserver.OutServer()

	def publish(self, pubdata):
		pass

	def put(self, pubdata):
		pass
