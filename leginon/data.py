#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginonconfig
import leginonobject
import Numeric
import strictdict
import warnings

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

	def getFactory(self, valuetype):
		if valuetype is DataDict:
			f = valuetype
		else:
			f = strictdict.TypedDict.getFactory(self, valuetype)
		return f

class UnknownData(object):
	'''
	this is a place holder for a Data instance that is not yet known
	'''
	def __init__(self, qikey):
		self.qikey = qikey

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

def data2dict(idata, noNone=False):
	d = {}
	for key,value in idata.items():
		if isinstance(value, Data):
			subd = data2dict(value, noNone)
			if subd:
				d[key] = subd
		else:
			if not noNone or value is not None:
				d[key] = value
	return d

class Data(DataDict, leginonobject.LeginonObject):
	'''
	Combines DataDict and LeginonObject to create the base class
	for all leginon data.  This can be initialized with keyword args
	as long as those keys are declared in the specific subclass of
	Data.  The special keyword 'initializer' can also be used
	to initialize with a dictionary.  If a key exists in both
	initializer and kwargs, the kwargs value is used.
	'''
	def __init__(self, **kwargs):
		DataDict.__init__(self)

		self.dbid = None

		# if initializer was given, update my values
		if 'initializer' in kwargs:
			self.update(kwargs['initializer'])
			del kwargs['initializer']

		# additional keyword arguments also update my values
		# (overriding anything set by initializer)
		self.update(kwargs)

		# LeginonObject base class needs id
		legid = self['id']
		leginonobject.LeginonObject.__init__(self, legid)

		## Database ID (primary key)
		## If this is None, then this data has not
		## been inserted into the database

	def __setitem__(self, key, value):
		'''
		'''
		### synch with leginonobject attributes
		if key == 'id':
			super(Data, self).__setattr__(key, value)
		elif key == 'session':
			if isinstance(value, SessionData):
				super(Data, self).__setattr__(key, value['name'])
			else:
				super(Data, self).__setattr__(key, value)
		DataDict.__setitem__(self, key, value)

		## reset dbid because data no longer matches database
		## Unfortunately, this does not cover all cases of
		## modifying the object, just at the top level.
		## Also, this is called more often than necessary because
		## of deepcopy, (maybe pickle??), etc, which do not intend
		## to modify the values, but trigger this anyway
		if self.dbid is not None:
			warnings.warn('__setitem__ on %s object that exists in DB...  dbid attribute will be reset' % (self.__class__), stacklevel=2)
		self.dbid = None

	def typemap(cls):
		t = DataDict.typemap()
		t += [('id', tuple)]
		return t
	typemap = classmethod(typemap)

	def getFactory(self, valuetype):
		try:
			mine = issubclass(valuetype, Data)
		except TypeError:
			mine = False

		if mine:
			def f(value):
				if isinstance(value, valuetype):
					return value
				elif isinstance(value, UnknownData):
					return value
				else:
					raise ValueError('must be type %s' % (valuetype,))
				
		else:
			f = DataDict.getFactory(self, valuetype)
		return f

	def toDict(self, noNone=False):
		return data2dict(self, noNone)

	def size(self):
		size = 0
		for key, datatype in self.types().items():
			if key in self and self[key] is not None:
				size += self.sizeof(self[key], datatype)
		return size

	def sizeof(self, value, datatype):
		if datatype == strictdict.NumericArrayType:
			return len(Numeric.ravel(value)) * value.itemsize()
		else:
			return 0

'''

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

'''

class GroupData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('description', str)]
		return t
	typemap = classmethod(typemap)
	
class UserData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('full name', str),
					('group', GroupData)]
		return t
	typemap = classmethod(typemap)

class InstrumentData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('description', str),
					('scope', str),
					('camera', str),
					('hostname', str),
					('camera size', int),
					('camera pixel size', float)]
		return t
	typemap = classmethod(typemap)

class SessionData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('user', UserData),
					('instrument', InstrumentData),
					('image path', str),
					('comment', str)]
		return t
	typemap = classmethod(typemap)

class InSessionData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('session', SessionData)]
		return t
	typemap = classmethod(typemap)

class EMData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [ ('system time', float)]
		return t
	typemap = classmethod(typemap)

scope_params = [
	('magnification', int),
	('spot size', int),
	('intensity', float),
	('image shift', dict),
	('beam shift', dict),
	('defocus', float),
	('focus', float),
	('reset defocus', int),
	('screen current', float), 
	('beam blank', str), 
	('stigmator', dict),
	('beam tilt', dict),
	('corrected stage position', int),
	('stage position', dict),
	('holder type', str),
	('holder status', str),
	('stage status', str),
	('vacuum status', str),
	('column valves', str),
	('column pressure', float),
	('turbo pump', str),
	('high tension', int),
	('screen position', str),
]
camera_params = [
	('dimension', dict),
	('binning', dict),
	('offset', dict),
	('exposure time', float),
	('exposure type', str),
	('image data', strictdict.NumericArrayType),
	('inserted', bool)
]

class ScopeEMData(EMData):
	def typemap(cls):
		t = EMData.typemap()
		t += scope_params
		return t
	typemap = classmethod(typemap)

class CameraEMData(EMData):
	def typemap(cls):
		t = EMData.typemap()
		t += camera_params
		return t
	typemap = classmethod(typemap)

class AllEMData(EMData):
	'''
	this includes everything from scope and camera
	'''
	def typemap(cls):
		t = EMData.typemap()
		t += scope_params
		t += camera_params
		return t
	typemap = classmethod(typemap)

class CameraConfigData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', float),
			('exposure type', str),
			('correct', int),
			('auto square', int),
			('auto offset', int),
		]
		return t
	typemap = classmethod(typemap)

class LocationData(InSessionData):
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

class NodeClassesData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [ ('nodeclasses', tuple), ]
		return t
	typemap = classmethod(typemap)

class DriftData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [('rows', float), ('cols', float)]
		return t
	typemap = classmethod(typemap)

class CalibrationData(InSessionData):
	pass

class CameraSensitivityCalibrationData(CalibrationData):
	def typemap(cls):
		t = CalibrationData.typemap()
		t += [
			('high tension', int),
			('sensitivity', int),
		]
		return t
	typemap = classmethod(typemap)

class MagDependentCalibrationData(CalibrationData):
	def typemap(cls):
		t = CalibrationData.typemap()
		t += [
			('magnification', int),
			('high tension', int),
		]
		return t
	typemap = classmethod(typemap)

class PixelSizeCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('pixelsize', float), ('comment', str)]
		return t
	typemap = classmethod(typemap)

class MatrixCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('type', str), ('matrix', strictdict.NumericArrayType), ]
		return t
	typemap = classmethod(typemap)

class MoveTestData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('move pixels x', float),
			('move pixels y', float),
			('move meters x', float),
			('move meters y', float),
			('error pixels x', float),
			('error pixels y', float),
			('error meters x', float),
			('error meters y', float),
		]
		return t
	typemap = classmethod(typemap)

class MatrixMoveTestData(MoveTestData):
	def typemap(cls):
		t = MoveTestData.typemap()
		t += [
			('calibration', MatrixCalibrationData),
		]
	typemap = classmethod(typemap)

class ModeledStageMoveTestData(MoveTestData):
	def typemap(cls):
		t = MoveTestData.typemap()
		t += [
			('model', StageModelCalibrationData),
			('mag only', StageModelMagCalibrationData),
		]
	typemap = classmethod(typemap)

class StageModelCalibrationData(CalibrationData):
	def typemap(cls):
		t = CalibrationData.typemap()
		t += [
			('label', str),
			('axis', str),
			('period', float),
			('a', strictdict.NumericArrayType),
			('b', strictdict.NumericArrayType)
		]
		return t
	typemap = classmethod(typemap)

class StageModelMagCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		t = MagDependentCalibrationData.typemap()
		t += [ ('label', str), ('axis', str), ('angle', float), ('mean',float)]
		return t
	typemap = classmethod(typemap)

class StageMeasurementData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('label', str),
			('magnification', int),
			('axis', str),
			('x',float),
			('y',float),
			('delta',float),
			('imagex',float),
			('imagey',float),
		]
		return t
	typemap = classmethod(typemap)

class PresetData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('name', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('eucentric focus', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', float),
			('removed', int),
			('hasref', bool),
			('dose', float),
		]
		return t
	typemap = classmethod(typemap)

class NewPresetData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
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
			('exposure time', float),
		]
		return t
	typemap = classmethod(typemap)

class PresetSequenceData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('sequence', list)
		]
		return t
	typemap = classmethod(typemap)

class CorrelationData(InSessionData):
	pass

class ImageData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('image', strictdict.NumericArrayType),
			('label', str),
			('filename', str),
		]
		return t
	typemap = classmethod(typemap)

	def path(self):
		'''
		create a directory for this image file if it does not exist.
		return the full path of this directory.
		'''
		impath = self['session']['image path']
		leginonconfig.mkdirs(impath)
		return impath

	def filename(self):
		'''
		create a unique filename for this image
		filename format:  [session]_[label]_[nodename]_[integer].mrc
		'''
		basename = self['session']['name']
		## use label if available, else use node name
		if self['label'] is not None:
			basename += '_%s' % (self['label'],)
		else:
			basename += '_%s' % (self['id'][-2],)
			
		myindex = self['id'][-1]
		basename += '_%06d.mrc' % (myindex,)
		return basename

	def thumb_filename(self):
		regular = self.filename()
		thumb = 'thumb_' + regular
		return thumb

class MosaicImageData(ImageData):
	'''Image of a mosaic'''
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('mosaic', MosaicData), ]
		t += [ ('scale', float), ]
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
		t += [ ('scope', ScopeEMData), ('camera', CameraEMData), ]
		return t
	typemap = classmethod(typemap)


## the camstate key is redundant (it's a subset of 'camera')
## but for now it helps to query the same way we used to
class CorrectorImageData(ImageData):
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('camstate', CorrectorCamstateData), ]
		return t
	typemap = classmethod(typemap)

class DarkImageData(CorrectorImageData):
	pass

class BrightImageData(CorrectorImageData):
	pass

class NormImageData(CorrectorImageData):
	pass

class MosaicData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('data IDs', list),
		]
		return t
	typemap = classmethod(typemap)

class StageLocationData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('removed', bool),
			('name', str),
			('comment', str),
			('x', float),
			('y', float),
			('z', float),
			('a', float),
			('xy only', bool),
		]
		return t
	typemap = classmethod(typemap)

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

class PresetReferenceImageData(PresetImageData):
	'''
	This is a reference image for getting stats at different presets
	'''
	pass

class AcquisitionImageData(PresetImageData):
	def typemap(cls):
		t = PresetImageData.typemap()
		t += [ ('target', AcquisitionImageTargetData), ]
		return t
	typemap = classmethod(typemap)

	def filename(self):
		if not self['filename']:
			raise RuntimeError('no filename set for this image')
		return self['filename'] + '.mrc'

class ProcessedAcquisitionImageData(ImageData):
	'''image that results from processing an AcquisitionImageData'''
	def typemap(cls):
		t = ImageData.typemap()
		t += [ ('source', AcquisitionImageData), ]
		return t
	typemap = classmethod(typemap)

	def filename(self):
		if not self['filename']:
			raise RuntimeError('no filename set for this image')
		return self['filename'] + '.mrc'

class AcquisitionFFTData(ProcessedAcquisitionImageData):
	'''Power Spectrum of AcquisitionImageData'''
	pass

class ScaledAcquisitionImageData(ImageData):
	'''Small version of AcquisitionImageData'''
	pass

class TrialImageData(PresetImageData):
	pass

class CorrectorPlanData(InSessionData):
	'''
	mosaic data contains data ID of images mapped to their 
	position and state.
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('camstate', CorrectorCamstateData),
			('bad_rows', tuple),
			('bad_cols', tuple),
			('clip_limits', tuple)
		]
		return t
	typemap = classmethod(typemap)

class CorrectorCamstateData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('dimension', dict),
			('binning', dict),
			('offset', dict),
		]
		return t
	typemap = classmethod(typemap)

class MosaicTargetData(InSessionData):
	'''
	this is an alias for an AcquisitionImageTargetData which is used
	to show a target in a full mosaic image
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('row', int),
		  ('column', int),
		  ('target', AcquisitionImageTargetData),
		]
		return t
	typemap = classmethod(typemap)

class GridData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('grid number', int),
					('grid tray ID', int)]
		return t
	typemap = classmethod(typemap)

class ImageTargetData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			# pixel delta to target from state in row, column
		  ('delta row', int),
		  ('delta column', int),
		  ('scope', ScopeEMData),
		  ('camera', CameraEMData),
		  ('preset', PresetData),
		  ('type', str),
		  ('version', int),
		  ('number', int),
		  ('status', str),
			('grid', GridData),
		]
		return t
	typemap = classmethod(typemap)

class ImageTargetShiftData(InSessionData):
	'''
	This keeps a dict of target shifts for a set of images.
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			('shifts', dict),
			('requested', bool),
		]
		return t
	typemap = classmethod(typemap)

class AcquisitionImageTargetData(ImageTargetData):
	def typemap(cls):
		t = ImageTargetData.typemap()
		t += [
		  ('image', AcquisitionImageData),
		  ## this could be generalized as total dose, from all
		  ## exposures on this target.  For now, this is just to
		  ## keep track of when we have done the melt ice thing.
		  ('pre_exposure', bool),
		]
		return t
	typemap = classmethod(typemap)

### XXX the list here has variable length
class ImageTargetListData(InSessionData):
	def typemap(cls):
		t = InSessionData.typemap()
		t += [ ('targets', list), ]
		return t
	typemap = classmethod(typemap)

class FocuserResultData(InSessionData):
	'''
	results of doing autofocus
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('target', AcquisitionImageTargetData),
		  ('defocus', float),
		  ('stigx', float),
		  ('stigy', float),
		  ('min', float),
		  ('stig correction', int),
		  ('defocus correction', str),
		]
		return t
	typemap = classmethod(typemap)

class EMTargetData(InSessionData):
	'''
	This is an ImageTargetData with deltas converted to new scope
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
			# pixel delta to target from state in row, column
		  ('scope', ScopeEMData),
		  ('preset', PresetData)
		]
		return t
	typemap = classmethod(typemap)

class ApplicationData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('name', str),
					('version', int)]
		return t
	typemap = classmethod(typemap)

class NodeSpecData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('class string', str),
					('alias', str),
					('launcher alias', str),
					('args', list),
					('new process flag', int),
					('dependencies', list),
					('application', ApplicationData)]
		return t
	typemap = classmethod(typemap)

class BindingSpecData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('event class string', str),
					('from node alias', str),
					('to node alias', str),
					('application', ApplicationData)]
		return t
	typemap = classmethod(typemap)

class DeviceGetData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('keys', list)]
		return t
	typemap = classmethod(typemap)

class DeviceData(Data):
	def typemap(cls):
		t = Data.typemap()
		return t
	typemap = classmethod(typemap)

# for testing
class DiaryData(InSessionData):
	'''
	User's diary entry
	'''
	def typemap(cls):
		t = InSessionData.typemap()
		t += [
		  ('message', str),
		]
		return t
	typemap = classmethod(typemap)


########## for testing

# new class of data
class MyData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('other', MyOtherData)]
		return t
	typemap = classmethod(typemap)

class MyOtherData(Data):
	def typemap(cls):
		t = Data.typemap()
		t += [('stuff', int)]
		t += [('encore', str)]
		return t
	typemap = classmethod(typemap)
