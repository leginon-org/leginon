
import leginonobject
import array

class Data(leginonobject.LeginonObject):
	'''baseclass for leginon data.  subclasses should implement content'''
	def __init__(self, id, content):
		leginonobject.LeginonObject.__init__(self, id)
		self.content = content

		## taking this out until it breaks something
		#self.origin = {}

class IntData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, int(content))


class StringData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, str(content))

class EMData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

# this is for the manager, it masquerades (sp?) as the data with the same id,
# but it contains the location of the data instead.
# the content is the list of locations the manager gets from the nodeid and
# its noderegistry
class LocationData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, content)

# nodeid is the dataid, content is dict with physical location
class NodeLocationData(LocationData):
	def __init__(self, id, content):
		LocationData.__init__(self, id, dict(content))
	def __repr__(self):
			return "<NodeLocationData for %s> %s" % (self.id, self.content)

# real dataid is the dataid, but content is actually a list of nodeids when
# the real data is located
class DataLocationData(LocationData):
	def __init__(self, id, content):
		LocationData.__init__(self, id, list(content))
	def __repr__(self):
			return "<DataLocationData for %s> %s" % (self.id, self.content)

