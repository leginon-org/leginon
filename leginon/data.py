
import leginonobject

class Data(leginonobject.LeginonObject):
	'''baseclass for leginon data.  subclasses should implement content'''
	def __init__(self, content):
		leginonobject.LeginonObject.__init__(self)
		self.content = content
		self.origin = {}


class IntData(Data):
	def __init__(self, content):
		Data.__init__(self, int(content))


class StringData(Data):
	def __init__(self, content):
		Data.__init__(self, str(content))

