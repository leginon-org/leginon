

import leginonobject, inhandler, outhandler

class DataServer(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.outhandler = outhandler.OutHandler()
		self.inhandler = inhandler.InHandler()

