
import leginonobject

class Data(leginonobject.LeginonObject):
	'''baseclass for leginon data.  subclasses should implement content'''
	def __init__(self, creator=None, content = None):
		leginonobject.LeginonObject.__init__(self)
		self.creator = creator
		self.content = content


class StringData(Data):
	def __init__(self, creator, content):
		if type(content) != str:
			raise TypeError('StringData content must be string')
		Data.__init__(self, creator, content)
