
import leginonobject
import array
import Numeric

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

class DBData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

# we're going to play with the image being a Numeric array, and hopefully
# type and dimenion can be extracted from only that
class ImageData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, content)

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

class NodeClassesData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, tuple(content))


# real dataid is the dataid, but content is actually a list of nodeids when
# the real data is located
class DataLocationData(LocationData):
	def __init__(self, id, content):
		LocationData.__init__(self, id, list(content))
	def __repr__(self):
			return "<DataLocationData for %s> %s" % (self.id, self.content)

class NumericData(Data):
	def __init__(self, id, content):
		if type(content) != Numeric.ArrayType:
			raise RuntimeError('content must be Numeric array')
		Data.__init__(self, id, content)

class DBRecordData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))
		# validate content
		if 'table' not in self.content:
			raise RuntimeError('invalid content for DBRecordData')
		if 'record' not in self.content:
			raise RuntimeError('invalid content for DBRecordData')
		# maybe check that 'record' contains a dict

class CorrelationData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class CorrelationImageData(ImageData):
	def __init__(self, id, content):
		ImageData.__init__(self, id, content)

class CrossCorrelationImageData(CorrelationImageData):
	def __init__(self, id, content):
		CorrelationImageData.__init__(self, id, content)

class PhaseCorrelationImageData(CorrelationImageData):
	def __init__(self, id, content):
		CorrelationImageData.__init__(self, id, content)

class ReferenceImageData(ImageData):
	def __init__(self, id, content):
		ImageData.__init__(self, id, content)

class DarkImageData(ReferenceImageData):
	def __init__(self, id, content):
		ReferenceImageData.__init__(self, id, content)

class BrightImageData(ReferenceImageData):
	def __init__(self, id, content):
		ReferenceImageData.__init__(self, id, content)


