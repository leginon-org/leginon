
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

class EMData(Data):
	def __init__(self, content):
		Data.__init__(self, dict(content))

# this is for the manager, it masquerades (sp?) as the data with the same id,
# but it contains the location of the data instead.
# the content is the list of locations the manager gets from the nodeid and
# its noderegistry
class LocationData(Data):
	def __init__(self, id, content):
		Data.__init__(self, list(content))
		self.id = id

