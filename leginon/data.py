#!/usr/bin/env python

import leginonobject
import array
import Numeric
import strictdict

## How to define a new leginon data type:
##   Subclass Data or a subclass of Data.  Override the typemap() class
## method to define the types of the items contained in the class
##   

class DataDict(strictdict.TypedDict):
	'''
	A wrapper around TypedDict that adds a class method: typemap()
	This class method is used to create the type_map_or_seq argument
	that is normally passed during instantiation.  We then remove this
	argument from the init method.  In other words,
	we are hard coding the TypedDict types into the class and making
	it easy to override these types in a subclass.

	The typemap() method should return the same information as the 
	types() method already provided by TypedDict.  The difference is
	that (as of now) types() returns a KeyedDict and typedict() 
	returns a list of tuples mapping.  Maybe this can be unified soon.
	Another key difference is that since typemap() is a class method,
	we can inquire about the types of a DataDict's contents without
	actually having an instance.  This might be useful for something
	like a database interface that needs to create tables from these
	classes.
	'''
	def __init__(self, map_or_seq=None):
		strictdict.TypedDict.__init__(self, map_or_seq, type_map_or_seq=self.typemap())

	def typemap(cls):
		'''
		Returns the mapping of keys to types for this class.
		  [(key, type), (key, type), ...]
		Override this in subclasses to specialize the contents
		of this type of data.
		'''
		return []
	typemap = classmethod(typemap)

class Data(DataDict, leginonobject.LeginonObject):
	'''
	Inherits DataDict and LeginonObject to for the base class
	for all leginon data.
	'''
	def __init__(self, id, initializer=None, **kwargs):
		# LeginonObject base class needs id
		leginonobject.LeginonObject.__init__(self, id)
		# DataDict base class
		DataDict.__init__(self)
		# initial values
		self['id'] = id
		if initializer is not None:
			self.update(initializer)
		self.update(kwargs)

	def typemap(cls):
		t = DataDict.typemap() + [('id', tuple)]
		return t
	typemap = classmethod(typemap)

class NewData(Data):
	'''
	Example of a new data type
	'''
	def __init__(self, id, initializer=None, **kwargs):
		Data.__init__(self, id, initializer, **kwargs)

	def typemap(cls):
		t1 = Data.typemap()
		t2 = [ ('stuff', int) ]
		return t1 + t2
	typemap = classmethod(typemap)


class OLDData(leginonobject.LeginonObject):
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
	'''
	self.content will be a dict with the following keys
	   'image':  the Numeric array representation of the image
	'''
	def __init__(self, id, image):
		content = {'image':image}
		Data.__init__(self, id, content)

class CameraImageData(ImageData):
	'''
	ImageData that originates from a camera
	self.content will be a dict with the following keys
	   'image':  the Numeric array representation of the image
	   'scope':  the microscope state (dict) at the time of acquisition
	   'camera':  the camera state (dict) at the time of acquisition
	'''
	def __init__(self, id, image, scope, camera):
		ImageData.__init__(self, id, image)
		self.content.update({'scope':scope, 'camera':camera})

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

class CalibrationData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, content)

class MatrixCalibrationData(CalibrationData):
	def __init__(self, id, matrix):
		try:
			matrixcontent = matrix.astype(Numeric.Float64)
			CalibrationData.__init__(self, id, matrixcontent)
		except AttributeError:
			print 'MatrixCalibrationData requires Numeric array'
			raise

class PresetData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class CorrelationData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class CorrelationImageData(ImageData):
	'''
	ImageData that results from a correlation of two images
	content has the following keys:
		'image': Numeric data	
		'subject1':  first image (data id) used in correlation
		'subject2':  second image (data id) used in correlation
	'''
	def __init__(self, id, image, subject1, subject2):
		ImageData.__init__(self, id, image)
		self.content.update({'subject1':subject1, 'subject2':subject2})

class CrossCorrelationImageData(CorrelationImageData):
	def __init__(self, id, image, subject1, subject2):
		CorrelationImageData.__init__(self, id, image, subject1, subject2)

class PhaseCorrelationImageData(CorrelationImageData):
	def __init__(self, id, image, subject1, subject2):
		CorrelationImageData.__init__(self, id, image, subject1, subject2)

class CorrectionImageData(CameraImageData):
	def __init__(self, id, image, scope, camera):
		CameraImageData.__init__(self, id, image, scope, camera)

class DarkImageData(CorrectionImageData):
	def __init__(self, id, image, scope, camera):
		CorrectionImageData.__init__(self, id, image, scope, camera)

class BrightImageData(CorrectionImageData):
	def __init__(self, id, image, scope, camera):
		CorrectionImageData.__init__(self, id, image, scope, camera)

class TileImageData(CameraImageData):
	'''Contains a 2-D Numeric array of the image data and a list of neighboring image tile ID's.'''
	def __init__(self, id, image, scope, camera, neighbortiles):
		CameraImageData.__init__(self, id, image, scope, camera)
		self.content.update({'neighbor tiles':neighbortiles})

class MosaicImageData(CameraImageData):
	def __init__(self, id, image, scope, camera):
		CameraImageData.__init__(self, id, image, scope, camera)
		## scope and camera may not be useful if the mosaic is
		## mangled too much, maybe something else useful to put
		## here

class PresetImageData(CameraImageData):
	'''
	Adds preset to CameraImageData
	Because of targeting issues, it is necessary to track the preset
	since it may be different that the assigned scope and camera
	'''
	def __init__(self, id, image, scope, camera, preset):
		CameraImageData.__init__(self, id, image, scope, camera)
		self.content.update({'preset':preset})

class StateMosaicData(Data):
	'''Contains data ID of images mapped to their position and state.'''
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class ImageTargetData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class ImageTargetListData(Data):
	def __init__(self, id, content):
		Data.__init__(self, id, list(content))

if __name__ == '__main__':
	id = (1,2)
	d = Data(id)
	print 'd', d
