
import leginonobject, inserver, inclient

class InHandler(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.inclient = inclient.InClient()
		self.inserver = inserver.InServer(self.dispatch)

	def get(self, dataid):
		newdata = None
		return newdata

	def dispatch(self, newdata):
		"""
		knows what to do with incoming data
		"""

