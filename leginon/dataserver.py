

import leginonobject, inserver, outserver

class DataServer(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.outserver = outserver.OutServer()
		self.inserver = inserver.InServer()

