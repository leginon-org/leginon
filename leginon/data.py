
import leginonobject
import array
import Numeric

class Data(leginonobject.LeginonObject):
	'''Baseclass for leginon data. Subclasses should implement content.'''
	def __init__(self, id, content):
		leginonobject.LeginonObject.__init__(self, id)
		self.content = content

class IntData(Data):
	'''Integer data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, int(content))

class StringData(Data):
	'''String data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, str(content))

class EMData(Data):
	'''EM data. Dictionary of keys to values.'''
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class DBData(Data):
	'''Database data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class ImageData(Data):
	'''Image data. Content is a 2-D Numeric array.'''
	def __init__(self, id, content):
		Data.__init__(self, id, content)

class LocationData(Data):
	'''Has data ID, but content is the location of the real data. Used by Manager.'''
	def __init__(self, id, content):
		Data.__init__(self, id, content)

class NodeLocationData(LocationData):
	'''Node ID is the data ID, but content is the location of the node. Used by Manager.'''
	def __init__(self, id, content):
		LocationData.__init__(self, id, dict(content))
	def __repr__(self):
			return "<NodeLocationData for %s> %s" % (self.id, self.content)

class NodeClassesData(Data):
	'''Node Classes data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, tuple(content))

class DataLocationData(LocationData):
	'''Has data ID, but content is a list of node IDs where the data is located. Used by Manager.'''
	def __init__(self, id, content):
		LocationData.__init__(self, id, list(content))
	def __repr__(self):
		'''Returns a readable format.'''
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

class ImageTileData(ImageData):
	'''Contains a 2-D Numeric array of the image data and a list of neighboring image tile ID's.'''
	def __init__(self, id, image, neighbortiles):
		ImageData.__init__(self, id,
			{'image': image, 'neighbor tiles': neighbortiles})

class StateImageTileData(ImageData):
	'''Contains a 2-D Numeric array of the image data, a list of neighboring image tile ID's, and [sub]state acquired at.'''
	def __init__(self, id, image, state, neighbortiles):
		ImageData.__init__(self, id,
			{'image': image, 'neighbor tiles': neighbortiles, 'state': state})

class StateMosaicData(Data):
	'''Contains data ID of images mapped to their position and state.'''
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

