#!/usr/bin/env python

import leginonobject
import array
import strictdict
import copy
import Mrc

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

	def factories(self, valuetype):
		if valuetype is DataDict:
			f = DataDict
		else:
			f = strictdict.TypedDict.factories(self, valuetype)
		return f

def replaceData(originaldata, func, memo=None):
	'''
	(this is confusing, difficult to describe)
	func is called on a copy of original data, but only after func 
	has already been called on all children of original data 
	which are themselves Data instances.  The children are replaced
	with 
	Before func is called on the copy of original Data instance, all the 
	children which are Data instances are replaced with the result of
	calling func on them.
	'''
	## create copy of originaldata, recursively replace each child 
	## with replaceData(child).  Which is similar to saying:
	## replace each child with func(child)

	d = id(originaldata)

	if memo is None:
		memo = {}
	if memo.has_key(d):
		return memo[d]

	## deepcopy makes our memo system fail because children
	## now have multiple copies
	#mycopy = copy.deepcopy(originaldata)

	## copy fails because originaldata's children are modified
	mycopy = copy.copy(originaldata)

	for key,value in mycopy.items():
		if isinstance(value, Data):
			mycopy[key] = replaceData(value, func, memo)
		else:
			mycopy[key] = value

	replacement = func(mycopy)

	memo[d] = replacement
	return replacement

def accumulateData(originaldata, func, memo=None):
	d = id(originaldata)

	if memo is None:
		memo = {}
	if memo.has_key(d):
		return None

	myresult = []
	for key,value in originaldata.items():
		if isinstance(value, Data):
			childresult = accumulateData(value, func, memo)
			if childresult is not None:
				myresult += childresult

	myresult = func(originaldata) + myresult

	memo[d] = myresult
	return myresult


class DataReference(dict):
	'''
	instances of DataReference can be used in place of the actual data
	when one Data object references another.
	'''
	pass


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

		# if initializer was given, update my values
		if initializer is not None:
			## initializer can be mapping or sequence
			## so it's easiest to let OrderedDict make
			## sure of that
			validinit = strictdict.OrderedDict(initializer)
			self.update(validinit)

		# initial values come from LeginonObject's attributes
		self['id'] = self.id
		self['session'] = self.session

		# additional keyword arguments also update my values
		self.update(kwargs)

	def typemap(cls):
		t = DataDict.typemap()
		t += [ ('id', tuple), ('session', str), ]
		return t
	typemap = classmethod(typemap)

	def replaceData(self, func):
		'''
		return a copy of self where all child Data instances
		have recursively been replaced by calling func on them
		and then func is called on the parent.
		'''
		mycopy = copy.deepcopy(self)
		return replaceData(mycopy, func)

	def split(self):
		'''
		return a list containing copies of self and all self's
		children Data instances.  The copies have had all contained
		Data instances replaced with DataReferences.
		'''
		self.split_list = []
		mycopy = copy.deepcopy(self)
		replaceData(mycopy, self.split_appender)
		print 'SPLIT', self.split_list
		return self.split_list
		
	def split_appender(self, datainstance):
		self.split_list.append(datainstance)
		return datainstance.reference()

	def factories(self, valuetype):
		if issubclass(valuetype, Data):
			def f(value):
				if isinstance(value, DataReference):
					return value
				elif isinstance(value, valuetype):
					return value
				else:
					raise ValueError('must be type %s' % (valuetype,))
				
		else:
			f = DataDict.factories(self, valuetype)
		return f

	def reference(self):
		'''
		return a DataReference to this instance
		'''
		dr = DataReference()
		dr['target'] = self
		return dr

## How to define a new leginon data type:
##   - Inherit Data or a subclass of Data.
##   - do not overload the __init__ method (unless you have a good reason)
##   - Override the typemap(cls) class method
##   - make sure typemap is defined as a classmethod:
##      typemap = classmethod(typemap)
##   - typemap() should return a sequence mapping, usually a list
##       of tuples:   [ (key, type), (key, type),... ]
## Examples:
class NewData(Data):
	'''
	Example of a new data type
	'''
	def typemap(cls):
		t = Data.typemap()
		t += [ ('stuff', int), ('thing', float), ]
		return t
	typemap = classmethod(typemap)

class OtherData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('newdata', NewData), ('mynum', int),]
		return t
	typemap = classmethod(typemap)

class MoreData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('newdata1', NewData), ('newdata2', NewData), ('otherdata', OtherData),]
		return t
	typemap = classmethod(typemap)
	
class EMData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('system time', float), ]
		return t
	typemap = classmethod(typemap)

### maybe split this up into scope and camera?
class ScopeEMData(EMData):
	def typemap(cls):
		t = Data.typemap()
		t += [ 
			('magnification', int),
			('spot size', int),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('reset defocus', int),
			('screen current', float), 
			('beam blank', str), 
			('intensity', float),
			('stigmator', dict),
			('beam tilt', dict),
			('magnification', int),
			('stage position', dict),
		]
		return t
	typemap = classmethod(typemap)

class CameraEMData(EMData):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('offset', dict),
			('dimension', dict),
			('binning', dict),
			('exposure time', float),
			('image data', strictdict.NumericArrayType),
		]
		return t
	typemap = classmethod(typemap)

class AllEMData(EMData):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('scope', ScopeEMData),
			('camera', CameraEMData),
		]
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

class DriftData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += []
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
		t += [ ('matrix', strictdict.NumericArrayType), ]
		return t
	typemap = classmethod(typemap)

class PresetData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [
			('name', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', int),
		]
		return t
	typemap = classmethod(typemap)

class NewPresetData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [
			('name', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', int),
		]
		return t
	typemap = classmethod(typemap)

class PresetSequenceData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [
			('sequence', list)
		]
		return t
	typemap = classmethod(typemap)

class CorrelationData(Data):
	pass

class ImageData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('image', strictdict.NumericArrayType), ]
		# for DB
		t += [ ('filename', str), ]
		return t
	typemap = classmethod(typemap)

	def save(self):
		'''
		saves an image to file and sets 'filename' accordingly
		'''
		numdata = self['image']
		session = self['session']
		id = self['id']
		idstrlist = [str(i) for i in id]
		idstr = '-'.join(idstrlist)

		if numdata is not None:
			# filename = ???
			try:
				filename = os.environ['LEGINONPATH'] + '/images/%s-%s.mrc' % (session, idstr)
			except:
				filename = './images/%s-%s.mrc' % (session, idstr)
			try:
				Mrc.numeric_to_mrc(numdata, filename)
			except:
				raise
				self.printerror('error converting image to file')
			self['filename'] = filename

	def load(self, filename=None):
		'''
		loads MRC image using either the 'filename' item of ImageData instance, or the specified 'filename' argument.
		'''
		if filename is not None:
			self['filename'] = filename
		if self['filename'] is None:
			raise RuntimeError('no filename specified for ImageData load')

		try:
			self['image'] = Mrc.mrc_to_numeric(self['filename'])
		except:
			self.printerror('error converting image from file')

		### Should this be done by the original caller or this method?
		### maybe there are nested ImageData instances in this one
		for thing in self.values():
			if isinstance(thing, ImageData):
				thing.load()

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
		t += [ ('scope', ScopeEMData), ('camera', CameraEMData), ]
		return t
	typemap = classmethod(typemap)

## the camstate key is redundant (it's a subset of 'camera')
## but for now it helps to query the same way we used to
class CorrectionImageData(CameraImageData):
	def typemap(cls):
		t = CameraImageData.typemap()
		t += [ ('camstate', CameraEMData), ]
		return t
	typemap = classmethod(typemap)

class DarkImageData(CorrectionImageData):
	pass

class BrightImageData(CorrectionImageData):
	pass

class NormImageData(CorrectionImageData):
	pass

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

class NewPresetImageData(CameraImageData):
	'''
	If an image was acquire using a certain preset, use this class
	to include the preset with it.
	'''
	def typemap(cls):
		t = CameraImageData.typemap()
		t += [ ('preset', NewPresetData), ]
		return t
	typemap = classmethod(typemap)

class TileImageData(PresetImageData):
	def typemap(cls):
		t = PresetImageData.typemap()
		t += [ ('neighbor_tiles', list), ]
		return t
	typemap = classmethod(typemap)

class AcquisitionImageData(PresetImageData):
	pass

class TrialImageData(PresetImageData):
	pass

class CorrectorPlanData(Data):
	'''
	mosaic data contains data ID of images mapped to their 
	position and state.
	'''
	def typemap(cls):
		t = Data.typemap()
		t += [
			('camstate', CameraEMData),
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

## this stuff came from ImageCanvas.eventXYInfo and ImageWatcher.imageInfo
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
		  ('scope', ScopeEMData),
		  ('camera', CameraEMData),
		  ('source', str),
		  ('preset', PresetData)
		]
		return t
	typemap = classmethod(typemap)

class FocusTargetData(ImageTargetData):
	pass

### XXX the list here has variable lenght
class ImageTargetListData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('targets', list), ]
		return t
	typemap = classmethod(typemap)

class PixelDriftData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [ ('rows', float), ]
		t += [ ('cols', float), ]
		return t
	typemap = classmethod(typemap)

