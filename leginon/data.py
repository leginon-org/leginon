#!/usr/bin/env python

import leginonobject
import array
import Numeric
import strictdict
import copy

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
			## initializer can be mapping or sequence
			## so it's easiest to let OrderedDict make
			## sure of that
			validinit = strictdict.OrderedDict(initializer)
			self.update(validinit)
		# additional keyword arguments also update my values
		self.update(kwargs)

	def typemap(cls):
		t = DataDict.typemap()
		t += [ ('id', tuple), ('session', str), ]
		return t
	typemap = classmethod(typemap)

	def __deepcopy__(self, memo):
		id_copy = copy.deepcopy(self.id, memo)
		initializer = self.items()
		initializer_copy = copy.deepcopy(initializer, memo)
		return self.__class__(id=id_copy, initializer=initializer_copy)

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
		t += [ ('stuff', int), ('thing', float), ]
		return t
	typemap = classmethod(typemap)

class NumericData(Data):
	'''
	Example of a new data type
	'''
	def typemap(cls):
		t = Data.typemap()
		t += [ ('array', Numeric.ArrayType), ]
		return t
	typemap = classmethod(typemap)

### maybe split this up into scope and camera?
class EMData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('em', dict), ]
		return t
	typemap = classmethod(typemap)

class LocationData(Data):
	pass

class NodeLocationData(LocationData):
	def typemap(cls):
		t = LocationData.typemap()
		t += [ ('location', dict), ]
		return t
	typemap = classmethod(typemap)

class DataLocationData(LocationData):
	def typemap(cls):
		t = LocationData.typemap()
		t += [ ('location', list), ]
		return t
	typemap = classmethod(typemap)

class NodeClassesData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('nodeclasses', tuple), ]
		return t
	typemap = classmethod(typemap)

class CalibrationData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('type', str), ]
		return t
	typemap = classmethod(typemap)

class MagDependentCalibrationData(CalibrationData):
	def typemap(cls):
		t = CalibrationData.typemap()
		t += [ ('magnification', int), ]
		return t
	typemap = classmethod(typemap)

class PixelSizeCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('pixelsize', float), ]
		return t
	typemap = classmethod(typemap)

class MatrixCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('matrix', Numeric.ArrayType), ]
		return t
	typemap = classmethod(typemap)

class PresetData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [
			('name', str),
			('spot size', int),
			('magnification', int),
			('image shift', dict),
			('beam shift', dict),
			('intensity', float),
			('defocus', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', int),
		]
		return t
	typemap = classmethod(typemap)

class CorrelationData(Data):
	pass

class ImageData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('image', Numeric.ArrayType), ]
		# for DB
		t += [ ('database filename', str), ]
		return t
	typemap = classmethod(typemap)

class CorrelationImageData(ImageData):
	'''
	ImageData that results from a correlation of two images
	content has the following keys:
		'image': Numeric data	
		'subject1':  first image (data id) used in correlation
		'subject2':  second image (data id) used in correlation
	'''
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('subject1', ImageData), ('subject2', ImageData), ]
		return t
	typemap = classmethod(typemap)

class CrossCorrelationImageData(CorrelationImageData):
	pass

class PhaseCorrelationImageData(CorrelationImageData):
	pass

class CameraImageData(ImageData):
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('scope', dict), ('camera', dict), ]
		return t
	typemap = classmethod(typemap)

## the camstate key is redundant (it's a subset of 'camera')
## but for now it helps to query the same way we used to
class CorrectionImageData(CameraImageData):
	def typemap(cls):
		t = CameraImageData.typemap()
		t += [ ('camstate', dict), ]
		return t
	typemap = classmethod(typemap)

class DarkImageData(CorrectionImageData):
	pass

class BrightImageData(CorrectionImageData):
	pass

class NormImageData(CorrectionImageData):
	pass

class TileImageData(CameraImageData):
	def typemap(cls):
		t = CameraImageData.typemap()
		t += [ ('neighbor_tiles', list), ]
		return t
	typemap = classmethod(typemap)

class MosaicImageData(CameraImageData):
	## scope and camera may not be useful if the mosaic is
	## mangled too much, maybe something else useful to put
	## here
	pass

class PresetImageData(CameraImageData):
	'''
	If an image was acquire using a certain preset, use this class
	to include the preset with it.
	'''
	def typemap(cls):
		t = CameraImageData.typemap()
		t += [ ('preset', PresetData), ]
		return t
	typemap = classmethod(typemap)

class CorrectorPlanData(Data):
	'''
	mosaic data contains data ID of images mapped to their 
	position and state.
	'''
	def typemap(cls):
		t = Data.typemap()
		t += [
			('camstate', dict),
			('bad_rows', tuple),
			('bad_cols', tuple),
			('clip_limits', tuple)
		]
		return t
	typemap = classmethod(typemap)

### XXX the dict here has variable lenght
class StateMosaicData(Data):
	'''
	mosaic data contains data ID of images mapped to their 
	position and state.
	'''
	def typemap(cls):
		t = Data.typemap()
		t += [ ('mosaic data', dict), ]
		return t
	typemap = classmethod(typemap)

## this stuff camera from ImageCanvas.eventXYInfo and ImageWatcher.imageInfo
## XXX preset may not always be set
class ImageTargetData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [
		  ('canvas x', int),
		  ('canvas y', int),
		  ('image x', int),
		  ('image y', int),
		  ('array shape', tuple),
		  ('array row', int),
		  ('array column', int),
		  ('array value', float),

		  ('image id', tuple),
		  ('scope', dict),
		  ('camera', dict),
		  ('source', str),
		  ('preset', PresetData)
		]
		return t
	typemap = classmethod(typemap)

### XXX the list here has variable lenght
class ImageTargetListData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('targets', list), ]
		return t
	typemap = classmethod(typemap)
