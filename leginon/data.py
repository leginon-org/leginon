
import leginonobject

class Data(leginonobject.LeginonObject):
	'''baseclass for leginon data.  subclasses should implement content'''
	def __init__(self, creator=None, content = None):
		leginonobject.LeginonObject.__init__(self)
		self.creator = creator
		self.content = None
    # hack
		self.data_id = "replace this data_id"

