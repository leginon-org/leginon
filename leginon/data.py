#!/usr/bin/env python

import leginonobject
import array
import Numeric
import strictdict

## Unresolved issue:
##  It would be nice if you could cast one Data type to another
##  Right now that will probably result in a key error

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
		self.__class__.typemap = classmethod(self.__class__.typemap)
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
	Combines DataDict and LeginonObject to create the base class
	for all leginon data.
	'''
	def __init__(self, id, initializer=None, **kwargs):
		# LeginonObject base class needs id
		leginonobject.LeginonObject.__init__(self, id)
		# DataDict base class
		DataDict.__init__(self)
		
		# initial values come from LeginonObject's attributes
		self['id'] = self.id
		self['session'] = self.session

		# if initializer was given, update my values
		if initializer is not None:
			self.update(initializer)
		# additional keyword arguments also update my values
		self.update(kwargs)

	def typemap(cls):
		t = DataDict.typemap()
		t += [
			('id', tuple),
			('session', str),
		]
		return t
	typemap = classmethod(typemap)

## How to define a new leginon data type:
##   - Inherit Data or a subclass of Data.
##   - do not overload the __init__ method (unless you have a good reason)
##   - Override the typemap(cls) class method
##   - make sure typemap is defined as a classmethod:
##      typemap = classmethod(typemap)
##   - typemap() should return a sequence mapping, usually a list
##       of tuples:   [ (key, type), (key, type),... ]

class NewData(Data):
	'''
	Example of a new data type
	'''
	def typemap(cls):
		t = Data.typemap()
		t += [
			('stuff', int),
			('thing', float),
		]
		return t
	typemap = classmethod(typemap)


class NumericData(Data):
	'''
	Example of a new data type
	'''
	def typemap(cls):
		t = Data.typemap()
		t += [
			('array', Numeric.ArrayType),
		]
		return t
	typemap = classmethod(typemap)


class ImageData(NumericData):
	'''
	Example of a new data type
	'''
	def typemap(cls):
		t = NumericData.typemap()
		t += [
			('numeric', NumericData),
		]
		return t
	typemap = classmethod(typemap)



class OLDData(leginonobject.LeginonObject):
	'''Baseclass for leginon data. Subclasses should implement content.'''
	def __init__(self, id, content):
		leginonobject.LeginonObject.__init__(self, id)
		self.content = content

class OLDIntData(OLDData):
	'''Integer data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, int(content))

class OLDStringData(OLDData):
	'''String data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, str(content))

class OLDEMData(OLDData):
	'''EM data. Dictionary of keys to values.'''
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class OLDDBData(OLDData):
	'''Database data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class OLDImageData(OLDData):
	'''
	self.content will be a dict with the following keys
	   'image':  the Numeric array representation of the image
	'''
	def __init__(self, id, image):
		content = {'image':image}
		Data.__init__(self, id, content)

class OLDCameraImageData(OLDImageData):
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

class OLDLocationData(OLDData):
	'''Has data ID, but content is the location of the real data. Used by Manager.'''
	def __init__(self, id, content):
		Data.__init__(self, id, content)

class OLDNodeLocationData(OLDLocationData):
	'''Node ID is the data ID, but content is the location of the node. Used by Manager.'''
	def __init__(self, id, content):
		LocationData.__init__(self, id, dict(content))
	def __repr__(self):
			return "<NodeLocationData for %s> %s" % (self.id, self.content)

class OLDNodeClassesData(OLDData):
	'''Node Classes data.'''
	def __init__(self, id, content):
		Data.__init__(self, id, tuple(content))

class OLDDataLocationData(OLDLocationData):
	'''Has data ID, but content is a list of node IDs where the data is located. Used by Manager.'''
	def __init__(self, id, content):
		LocationData.__init__(self, id, list(content))
	def __repr__(self):
		'''Returns a readable format.'''
		return "<DataLocationData for %s> %s" % (self.id, self.content)

class OLDNumericData(OLDData):
	def __init__(self, id, content):
		if type(content) != Numeric.ArrayType:
			raise RuntimeError('content must be Numeric array')
		Data.__init__(self, id, content)

class OLDDBRecordData(OLDData):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))
		# validate content
		if 'table' not in self.content:
			raise RuntimeError('invalid content for DBRecordData')
		if 'record' not in self.content:
			raise RuntimeError('invalid content for DBRecordData')
		# maybe check that 'record' contains a dict

class OLDCalibrationData(OLDData):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class OLDMatrixCalibrationData(OLDCalibrationData):
	EXAMPLE = {
		'magnification': 5,
		'type': 'test',
		'matrix': Numeric.array([[1.0,2.0],[3.0,4.0]], Numeric.Float64)
	}
	def __init__(self, id, magnification, type, matrix):
		try:
			if matrix.shape != (2,2):
				raise ValueError('matrix must be 2x2')
			matrixcontent = matrix.astype(Numeric.Float64)
		except AttributeError:
			print 'MatrixCalibrationData requires Numeric array'
			raise TypeError('matrix must be 2x2 Numeric array')

		content = {'magnification': int(magnification), 'type': str(type), 'matrix': matrixcontent}
		CalibrationData.__init__(self, id, content)

class OLDPresetData(OLDData):
	EXAMPLE = {
		'spot size': 5,
		'magnification': 50,
		'image shift': {'x': 0.555, 'y': 0.888},
		'beam shift': {'x': 0.555, 'y': 0.888},
		'intensity': 0.555,
		'defocus': -2e-6,

		'dimension': {'x': 512, 'y': 512},
		'binning': {'x': 2, 'y': 2},
		'offset': {'x':512, 'y':300},
		'exposure time': 500
	}
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class OLDCorrelationData(OLDData):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class OLDCorrelationImageData(OLDImageData):
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

class OLDCrossCorrelationImageData(OLDCorrelationImageData):
	def __init__(self, id, image, subject1, subject2):
		CorrelationImageData.__init__(self, id, image, subject1, subject2)

class OLDPhaseCorrelationImageData(OLDCorrelationImageData):
	def __init__(self, id, image, subject1, subject2):
		CorrelationImageData.__init__(self, id, image, subject1, subject2)

class OLDCorrectionImageData(OLDCameraImageData):
	def __init__(self, id, image, scope, camera):
		CameraImageData.__init__(self, id, image, scope, camera)

class OLDDarkImageData(OLDCorrectionImageData):
	def __init__(self, id, image, scope, camera):
		CorrectionImageData.__init__(self, id, image, scope, camera)

class OLDBrightImageData(OLDCorrectionImageData):
	def __init__(self, id, image, scope, camera):
		CorrectionImageData.__init__(self, id, image, scope, camera)

class OLDTileImageData(OLDCameraImageData):
	'''Contains a 2-D Numeric array of the image data and a list of neighboring image tile ID's.'''
	def __init__(self, id, image, scope, camera, neighbortiles):
		CameraImageData.__init__(self, id, image, scope, camera)
		self.content.update({'neighbor tiles':neighbortiles})

class OLDMosaicImageData(OLDCameraImageData):
	def __init__(self, id, image, scope, camera):
		CameraImageData.__init__(self, id, image, scope, camera)
		## scope and camera may not be useful if the mosaic is
		## mangled too much, maybe something else useful to put
		## here

class OLDPresetImageData(OLDCameraImageData):
	'''
	Adds preset to CameraImageData
	Because of targeting issues, it is necessary to track the preset
	since it may be different that the assigned scope and camera
	'''
	def __init__(self, id, image, scope, camera, preset):
		CameraImageData.__init__(self, id, image, scope, camera)
		self.content.update({'preset':preset})

class OLDStateMosaicData(OLDData):
	'''Contains data ID of images mapped to their position and state.'''
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class OLDImageTargetData(OLDData):
	def __init__(self, id, content):
		Data.__init__(self, id, dict(content))

class OLDImageTargetListData(OLDData):
	def __init__(self, id, content):
		Data.__init__(self, id, list(content))

if __name__ == '__main__':
	id = (1,2)
	d = Data(id)
	print 'd', d
