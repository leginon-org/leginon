# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import leginonconfig
import sinedon.newdict
import sinedon.data
import os
from pyami import weakattr
import projectdata

Data = sinedon.data.Data

class GroupData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('description', str),
			('privilege', projectdata.privileges),
		)
	typemap = classmethod(typemap)

class UserData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('username', str),
			('firstname', str),
			('lastname', str),
			('password', str),
			('email', str),
			('group', GroupData),
			('noleginon', bool),
			('advanced', bool),
		)
	typemap = classmethod(typemap)

class InstrumentData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('hostname', str),
			('cs', float),
			('pixelmax', int),
			#('type', str),
		)
	typemap = classmethod(typemap)

class MagnificationsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('instrument', InstrumentData),
			('magnifications', list),
		)
	typemap = classmethod(typemap)

class MainScreenScaleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('instrument', InstrumentData),
			('scale', float),
		)
	typemap = classmethod(typemap)

class ReferenceSessionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', SessionData),
		)
	typemap = classmethod(typemap)

class SessionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('user', UserData),
			('image path', str),
			('frame path', str),
			('comment', str),
			('holder', GridHolderData),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class SessionReservationData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('reserved', bool),
		)
	typemap = classmethod(typemap)

class GridHolderData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
		)
	typemap = classmethod(typemap)

class InSessionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', SessionData),
		)
	typemap = classmethod(typemap)

class QueueData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('label', str),
		)
	typemap = classmethod(typemap)

class EMData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('system time', float),
		)
	typemap = classmethod(typemap)

scope_params = (
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
	('main screen position', str),
	('main screen magnification', int),
	('small screen position', str),
	('low dose', str),
	('low dose mode', str),
	('film stock', int),
	('film exposure number', int),
	('pre film exposure', bool),
	('post film exposure', bool),
	('film exposure', bool),
	('film exposure type', str),
	('film exposure time', float),
	('film manual exposure time', float),
	('film automatic exposure time', float),
	('film text', str),
	('film user code', str),
	('film date type', str),
	('objective current', float),
	('exp wait time', float),
	('tem energy filtered', bool),
	('tem energy filter', bool),
	('tem energy filter width', float),
	('aperture size', dict),
	('probe mode', str),
)
camera_params = (
	('dimension', dict),
	('binning', dict),
	('binned multiplier', float),
	('offset', dict),
	('exposure time', float),
	('exposure type', str),
	('exposure timestamp', float),
	('inserted', bool),
	('dump', bool),
	('pixel size', dict),
	('energy filtered', bool),
	('energy filter', bool),
	('energy filter width', float),
	('nframes', int),
	('save frames', bool),
	('align frames', bool),
	('align filter', str),
	('frames name', str),
	('use frames', tuple),
	('frame time', float),
	('frame flip', bool),
	('frame rotate', int),
	('temperature', float),
	('temperature status', str),
	('readout delay', int),
	('gain index', int),
	('system corrected', bool),
)

class ScopeEMData(EMData):
	def typemap(cls):
		return EMData.typemap() + scope_params + (
			('tem', InstrumentData),
		)
	typemap = classmethod(typemap)

manacqparams = (
	'magnification',
	'spot size',
	'intensity',
	'image shift',
	'beam shift',
	'stage position',
	'high tension',
	'defocus',
)
class ManualAcquisitionScopeEMData(ScopeEMData):
	def typemap(cls):
		scopemap = ScopeEMData.typemap()
		mymap = []
		for item in scopemap:
			if item[0] in manacqparams:
				mymap.append(item)
		mymap = tuple(mymap)
		return EMData.typemap() + mymap + (
			('tem', InstrumentData),
		)
	typemap = classmethod(typemap)

class CameraEMData(EMData):
	def typemap(cls):
		return EMData.typemap() + camera_params + (
			('ccdcamera', InstrumentData),
		)
	typemap = classmethod(typemap)

class DriftMonitorRequestData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('emtarget', EMTargetData),
			('presetname', str),
			('threshold', float),
		)
	typemap = classmethod(typemap)

class DriftMonitorResultData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('status', str),
			('final', DriftData),
		)
	typemap = classmethod(typemap)

class LocationData(InSessionData):
	pass

class NodeLocationData(LocationData):
	def typemap(cls):
		return LocationData.typemap()  + (
			('location', dict),
			('class string', str),
		)
	typemap = classmethod(typemap)

class NodeClassesData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('nodeclasses', tuple),
		)
	typemap = classmethod(typemap)

class DriftData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('rows', float),
			('cols', float),
			('rowmeters', float),
			('colmeters', float),
			('interval', float),
			('target', AcquisitionImageTargetData),
			('scope', ScopeEMData),
			('camera', CameraEMData),
		)
	typemap = classmethod(typemap)

class DriftDeclaredData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('system time', float),
			('type', str),
			('node', str),
		)
	typemap = classmethod(typemap)

class TransformDeclaredData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('type', str),
			('node', str),
		)
	typemap = classmethod(typemap)

class TransformData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('rotation', float),
			('scale', float),
			('translation', dict),
		)
	typemap = classmethod(typemap)

class LogPolarTransformData(TransformData):
	def typemap(cls):
		return TransformData.typemap() + (
			('RS peak value', float),
			('T peak value', float),
		)
	typemap = classmethod(typemap)

class LogPolarGridTransformData(LogPolarTransformData):
	def typemap(cls):
		return LogPolarTransformData.typemap() + (
			('grid 1', GridData),
			('grid 2', GridData),
		)
	typemap = classmethod(typemap)

class MagnificationComparisonData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tem', InstrumentData),
			('maghigh', float),
			('maglow', float),
			('rotation', float),
			('scale', float),
			('shiftrow', float),
			('shiftcol', float),
		)
	typemap = classmethod(typemap)

class CalibrationData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tem', InstrumentData),
			('ccdcamera', InstrumentData),
		)
	typemap = classmethod(typemap)

class CameraSensitivityCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('high tension', int),
			('sensitivity', float),
		)
	typemap = classmethod(typemap)

class MagDependentCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('magnification', int),
			('high tension', int),
		)
	typemap = classmethod(typemap)

class BeamSizeCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('probe mode', str),
			('spot size', int),
			('c2 size', int),
			('focused beam', float),
			('scale', float),
		)
	typemap = classmethod(typemap)

class PixelSizeCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('pixelsize', float),
			('comment', str),
		)
	typemap = classmethod(typemap)

class BeamProbeDependentCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('probe', str),
		)
	typemap = classmethod(typemap)

class EucentricFocusData(BeamProbeDependentCalibrationData):
	def typemap(cls):
		return BeamProbeDependentCalibrationData.typemap() + (
			('focus', float),
		)
	typemap = classmethod(typemap)

class RotationCenterData(BeamProbeDependentCalibrationData):
	def typemap(cls):
		return BeamProbeDependentCalibrationData.typemap() + (
			('beam tilt', dict),
		)
	typemap = classmethod(typemap)

class MatrixCalibrationData(BeamProbeDependentCalibrationData):
	def typemap(cls):
		return BeamProbeDependentCalibrationData.typemap() + (
			('type', str),
			('matrix', sinedon.newdict.DatabaseArrayType),
			('previous', MatrixCalibrationData),
		)
	typemap = classmethod(typemap)

class MoveTestData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('move pixels x', float),
			('move pixels y', float),
			('move meters x', float),
			('move meters y', float),
			('error pixels x', float),
			('error pixels y', float),
			('error meters x', float),
			('error meters y', float),
		)
	typemap = classmethod(typemap)

class MatrixMoveTestData(MoveTestData):
	def typemap(cls):
		return MoveTestData.typemap() + (
			('calibration', MatrixCalibrationData),
		)
	typemap = classmethod(typemap)

class ModeledStageMoveTestData(MoveTestData):
	def typemap(cls):
		return MoveTestData.typemap() + (
			('model', StageModelCalibrationData),
			('mag only', StageModelMagCalibrationData),
		)
	typemap = classmethod(typemap)

class StageReproducibilityData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('label', str),
			('move x', float),
			('move y', float),
			('error pixels r', float),
			('error pixels c', float),
			('error meters', float),
		)
	typemap = classmethod(typemap)

class StageModelCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('label', str),
			('axis', str),
			('period', float),
			('a', sinedon.newdict.DatabaseArrayType),
			('b', sinedon.newdict.DatabaseArrayType),
		)
	typemap = classmethod(typemap)

class StageModelMagCalibrationData(MagDependentCalibrationData):
	def typemap(cls):
		return MagDependentCalibrationData.typemap() + (
			('label', str),
			('axis', str),
			('angle', float),
			('mean',float),
		)
	typemap = classmethod(typemap)

class StageMeasurementData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('label', str),
			('high tension', int),
			('magnification', int),
			('axis', str),
			('x',float),
			('y',float),
			('delta',float),
			('imagex',float),
			('imagey',float),
		)
	typemap = classmethod(typemap)

class PresetData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('number', int),
			('name', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('defocus', float),
			('defocus range min', float),
			('defocus range max', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('exposure time', float),
			('removed', bool),
			('hasref', bool),
			('dose', float),
			('film', bool),
			('tem', InstrumentData),
			('ccdcamera', InstrumentData),
			('tem energy filter', bool),
			('tem energy filter width', float),
			('energy filter', bool),
			('energy filter width', float),
			('aperture size', dict),
			('pre exposure', float),
			('skip', bool),
			('alt channel', bool),
			('save frames', bool),
			('frame time', float),
			('align frames', bool),
			('align filter', str),
			('use frames', tuple),
			('readout delay', int),
			('probe mode', str),
		)
	typemap = classmethod(typemap)

def createCommonSubclass(baseclass, otherclass):
	class NewClass(baseclass):
		def typemap(cls):
			ptypemap = otherclass.typemap()
			stypemap = baseclass.typemap()
			mytypemap = []
			for sitem in stypemap:
				sname = sitem[0]
				for pitem in ptypemap:
					pname = pitem[0]
					if sname == pname:
						mytypemap.append(sitem)
						break
			return tuple(mytypemap)
		typemap = classmethod(typemap)
	return NewClass

PresetScopeEMData = createCommonSubclass(ScopeEMData, PresetData)
PresetCameraEMData = createCommonSubclass(CameraEMData, PresetData)

class NavigatorScopeEMData(PresetScopeEMData):
	def typemap(cls):
		return PresetScopeEMData.typemap() + (
			('stage position', dict),
		)
	typemap = classmethod(typemap)

class NewPresetData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
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
		)
	typemap = classmethod(typemap)

class ImageData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', sinedon.newdict.MRCArrayType),
			('pixeltype', str),
			('pixels', int),
			('label', str),
			('filename', str),
			('list', ImageListData),
			('queue', QueueData),
		)
	typemap = classmethod(typemap)

	def getpath(self):
		'''return image path for this image'''
		try:
			impath = self['session']['image path']
			impath = leginonconfig.mapPath(impath)
		except:
			raise
			impath = os.path.abspath(os.path.curdir)
		return impath

	def mkpath(self):
		'''
		create a directory for this image file if it does not exist.
		return the full path of this directory.
		'''
		impath = self.getpath()
		leginonconfig.mkdirs(impath)
		return impath

	def filename(self):
		if not self['filename']:
			raise RuntimeError('"filename" not set for this image')
		return self['filename'] + '.mrc'

## this is not so important now that mosaics are created dynamically in
## DB viewer
class MosaicImageData(ImageData):
	'''Image of a mosaic'''
	def typemap(cls):
		return ImageData.typemap() + (
			('images', ImageListData),
			('scale', float),
		)
	typemap = classmethod(typemap)

class CameraImageData(ImageData):
	def typemap(cls):
		return ImageData.typemap() + (
			('scope', ScopeEMData),
			('camera', CameraEMData),
			('corrector plan', CorrectorPlanData),
			('correction channel', int), # used in AcquisitionImageData
			('channel', int), # used in ReferenceImagedata
			('dark', DarkImageData),
			('bright', BrightImageData),
			('norm', NormImageData),
			('use frames', tuple),
		)
	typemap = classmethod(typemap)

	def attachPixelSize(self):
		## get info for query from scope,camera
		scope = self['scope']
		camera = self['camera']
		tem = scope['tem']
		ccd = camera['ccdcamera']
		binningx = camera['binning']['x']
		binningy = camera['binning']['y']
		mag = scope['magnification']

		## do query
		q = PixelSizeCalibrationData()
		q['tem'] = tem
		q['ccdcamera'] = ccd
		q['magnification'] = mag
		results = q.query(results=1)
		if not results:
			return
		psize = results[0]['pixelsize']

		## attach pixel size to numpy array
		psizex = binningx * psize * 1e10
		psizey = binningy * psize * 1e10
		weakattr.set(self['image'], 'pixelsize', {'x':psizex,'y':psizey})

class CorrectorImageData(CameraImageData):
	pass

class DarkImageData(CorrectorImageData):
	pass

class BrightImageData(CorrectorImageData):
	pass

class NormImageData(CorrectorImageData):
	pass

class CorrectionImageSet(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('scope', ScopeEMData),
			('camera', CameraEMData),
			('channel', int),
		)
	typemap = classmethod(typemap)

class CorrectionImageData(ImageData):
	def typemap(cls):
		return ImageData.typemap() + (
			('set', CorrectionImageSet),
			('type', str),
		)
	typemap = classmethod(typemap)

class MosaicTileData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('list', ImageListData),
			('image', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class StageLocationData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('removed', bool),
			('name', str),
			('comment', str),
			('x', float),
			('y', float),
			('z', float),
			('a', float),
			('xy only', bool),
		)
	typemap = classmethod(typemap)

class AcquisitionImageData(CameraImageData):
	def typemap(cls):
		return CameraImageData.typemap() + (
			('preset', PresetData),
			('target', AcquisitionImageTargetData),
			('emtarget', EMTargetData),
			('grid', GridData),
			('spotmap', SpotWellMapData),
			('tilt series', TiltSeriesData),
			('version', int),
			('tiltnumber', int),
			('mover', MoverParamsData),
		)
	typemap = classmethod(typemap)

class DoseImageData(CameraImageData):
	def typemap(cls):
		return CameraImageData.typemap() + (
			('preset', PresetData),
		)
	typemap = classmethod(typemap)

class ViewerImageStatus(Data):
	def typemap(cls):
		return Data.typemap() + (
			('status', str),
			('image', AcquisitionImageData),
			('session', SessionData),
		)
	typemap = classmethod(typemap)

class AcquisitionImageStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('min', float),
			('max', float),
			('mean', float),
			('stdev', float),
		)
	typemap = classmethod(typemap)

## actually, this has only some things in common with AcquisitionImageData
## but enough that it is easiest to inherit it
class FilmData(AcquisitionImageData):
	pass

class ProcessedAcquisitionImageData(ImageData):
	'''image that results from processing an AcquisitionImageData'''
	def typemap(cls):
		return ImageData.typemap() + (
			('source', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class AcquisitionFFTData(ProcessedAcquisitionImageData):
	'''Power Spectrum of AcquisitionImageData'''
	pass

class ImageListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('targets', ImageTargetListData),
		)
	typemap = classmethod(typemap)

class CorrectorPlanData(InSessionData):
	'''
	mosaic data contains data ID of images mapped to their 
	position and state.
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('camera', CameraEMData),
			('bad_rows', tuple),
			('bad_cols', tuple),
			('bad_pixels', tuple),
			('clip_limits', tuple),
			('despike', bool),
			('despike size', int),
			('despike threshold', float),
		)
	typemap = classmethod(typemap)

class GridData(Data):
	'''
	This identifies a particular insertion of an EMGrid
	'''
	def typemap(cls):
		return Data.typemap() + (
			('grid ID', int),
			('insertion', int),
			('emgrid', EMGridData),
		)
	typemap = classmethod(typemap)

class EMGridData(Data):
	'''
	This identifies a physical EM grid prepared for a project
	'''
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('project', int),
			('mapping', WellMappingTypeData),
			('well group', int),
			('print trial', int),
			('plate', PrepPlateData),
		)
	typemap = classmethod(typemap)

class WellMappingTypeData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('plate format',PrepPlateFormatData),
			('grid format',EMGridFormatData),
		)
	typemap = classmethod(typemap)

class PrepPlateFormatData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('rows', int),
			('cols', int),
		)
	typemap = classmethod(typemap)

class EMGridFormatData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('rows', int),
			('cols', int),
			('skips', list),#list of tuples in (row,col), count from (1,1)
		)
	typemap = classmethod(typemap)

class SpotWellMapData(Data):
	'''
	Mapping between a plate position to a spot on an em grid at given well group
	Well and Spot positions are dictionaries of keys (row,col)
	'''
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('well position', dict),
			('spot position', dict),
			('mapping', WellMappingTypeData),
			('well group', int),
		)
	typemap = classmethod(typemap)

class PrepPlateData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('plate format',PrepPlateFormatData),
			('project', int),
		)
	typemap = classmethod(typemap)

class ImageTargetData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('delta row', float),
			('delta column', float),
			('scope', ScopeEMData),
			('camera', CameraEMData),
			('preset', PresetData),
			('type', str),
			('version', int),
			('number', int),
			('status', str),
			('grid', GridData),
			('list', ImageTargetListData),
		)
	typemap = classmethod(typemap)

class AcquisitionImageTargetData(ImageTargetData):
	def typemap(cls):
		return ImageTargetData.typemap() + (
			('image', AcquisitionImageData),
			## this could be generalized as total dose, from all
			## exposures on this target.  For now, this is just to
			## keep track of when we have done the melt ice thing.
			('pre_exposure', bool),
			('fromtarget', AcquisitionImageTargetData),
			# target mapping to a well on the prep plate if applicable
			('spotmap', SpotWellMapData),
			('last_focused', ImageTargetListData),
		)
	typemap = classmethod(typemap)

class ReferenceTargetData(ImageTargetData):
	def typemap(cls):
		return ImageTargetData.typemap() + (
			('image', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class ReferenceRequestData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('preset', str),
		)
	typemap = classmethod(typemap)

class AlignZeroLossPeakData(ReferenceRequestData):
	pass

class ZeroLossCheckData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('reference', ReferenceTargetData),
			('preset', PresetData),
			('mean', float),
			('std', float),
		)
	typemap = classmethod(typemap)

class MeasureDoseData(ReferenceRequestData):
	pass

class AdjustPresetData(ReferenceRequestData):
	pass

class FixBeamData(AdjustPresetData):
	pass

class ImageTargetListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('label', str),
			('mosaic', bool),
			('image', AcquisitionImageData),
			('queue', QueueData),
			('sublist', bool),
		)
	typemap = classmethod(typemap)

class DequeuedImageTargetListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('queue', QueueData),
			('list', ImageTargetListData),
		)
	typemap = classmethod(typemap)

class FocuserResultData(InSessionData):
	'''
	results of doing autofocus
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('target', AcquisitionImageTargetData),
			('preset', PresetData),
			('defocus', float),
			('stigx', float),
			('stigy', float),
			('min', float),
			('stig correction', int),
			('defocus correction', str),
			('method', str),
			('status', str),
			('drift', DriftData),
			('scope', ScopeEMData),
		)
	typemap = classmethod(typemap)

class EMTargetData(InSessionData):
	'''
	This is an ImageTargetData with deltas converted to new scope
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('preset', PresetData),
			('movetype', str),
			('image shift', dict),
			('beam shift', dict),
			('stage position', dict),
			('target', AcquisitionImageTargetData),
			('delta z', float),
		)
	typemap = classmethod(typemap)

class ApplicationData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('version', int),
			('hide', bool),
		)
	typemap = classmethod(typemap)

class NodeSpecData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('class string', str),
			('alias', str),
			('launcher alias', str),
			('dependencies', list),
			('application', ApplicationData),
		)
	typemap = classmethod(typemap)

class BindingSpecData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('event class string', str),
			('from node alias', str),
			('to node alias', str),
			('application', ApplicationData),
		)
	typemap = classmethod(typemap)

class LaunchedApplicationData(InSessionData):
	'''
	created each time an application is launched
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('application', ApplicationData),
			('launchers', list),
		)
	typemap = classmethod(typemap)

class DeviceGetData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('keys', list),
		)
	typemap = classmethod(typemap)

class DeviceData(Data):
	pass


class HoleFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('user-check', bool),
			('skip-auto', bool),
			('queue', bool),
			('edge-lpf-on', bool),
			('edge-lpf-size', int),
			('edge-lpf-sigma', float),
			('edge-filter-type', str),
			('edge-threshold', float),
			('template-rings', tuple),
			('template-correlation-type', str),
			('template-lpf', float),
			('threshold-value', float),
			('threshold-method', str),
			('blob-border', int),
			('blob-max-number', int),
			('blob-max-size', int),
			('blob-min-size', int),
			('lattice-spacing', float),
			('lattice-tolerance', float),
			('stats-radius', float),
			('ice-zero-thickness', float),
			('ice-min-thickness', float),
			('ice-max-thickness', float),
			('ice-max-stdev', float),
			('template-on', bool),
			('template-focus', tuple),
			('template-acquisition', tuple),
			('template-diameter', int),
			('file-diameter', int),
			('template-filename', str),
		)
	typemap = classmethod(typemap)

class HoleDepthFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('untilt-hole-image', AcquisitionImageData),
			('tilt-hole-image', AcquisitionImageData),
			('I-image', AcquisitionImageData),
			('I0-image', AcquisitionImageData),
			('edge-lpf-on', bool),
			('edge-lpf-size', int),
			('edge-lpf-sigma', float),
			('edge-filter-type', str),
			('edge-threshold', float),
			('template-rings', tuple),
			('template-correlation-type', str),
			('template-lpf', float),
			('template-tilt-axis', float),
			('threshold-value', float),
			('blob-border', int),
			('blob-max-number', int),
			('blob-max-size', int),
			('blob-min-size', int),
			('stats-radius', float),
			('ice-zero-thickness', float),
		)
	typemap = classmethod(typemap)

class HoleStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('prefs', HoleFinderPrefsData),
			('row', int),
			('column', int),
			('mean', float),
			('stdev', float),
			('thickness-mean', float),
			('thickness-stdev', float),
			('good', bool),
		)
	typemap = classmethod(typemap)

class HoleDepthStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('prefs', HoleDepthFinderPrefsData),
			('row', int),
			('column', int),
			('mean', float),
			('thickness-mean', float),
			('blobs-axis', float),
			('holedepth', float),
		)
	typemap = classmethod(typemap)

class SquareFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', MosaicImageData),
			('lpf-size', float),
			('lpf-sigma', float),
			('threshold', float),
			('border', int),
			('maxblobs', int),
			('minblobsize', int),
			('maxblobsize', int),
			('mean-min', int),
			('mean-max', int),
			('std-min', int),
			('std-max', int),
		)
	typemap = classmethod(typemap)

class SquareStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('prefs', SquareFinderPrefsData),
			('row', int),
			('column', int),
			('mean', float),
			('stdev', float),
			('good', bool),
		)
	typemap = classmethod(typemap)

class SettingsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('name', str),
			('isdefault', bool),
		)
	typemap = classmethod(typemap)

class ConnectToClientsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('clients', list),
			('localhost', str),
			('installation', str),
			('version', str),
		)
	typemap = classmethod(typemap)

class SetupWizardSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('session type', str),
			('selected session', str),
			('limit', bool),
			('n limit', int),
			('connect', bool),
			('c2 size', int),
		)
	typemap = classmethod(typemap)

class CameraSettingsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('dimension', dict),
			('offset', dict),
			('binning', dict),
			('exposure time', float),
			('save frames', bool),
			('frame time', float),
			('align frames', bool),
			('align filter', str),
			('use frames', tuple),
			('readout delay', int),
		)
	typemap = classmethod(typemap)

class MosaicTargetMakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('preset', str),
			('label', str),
			('radius', float),
			('overlap', float),
			('max targets', int),
			('max size', int),
			('mosaic center', str),
			('ignore request', bool),
		)
	typemap = classmethod(typemap)

class AtlasTargetMakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('preset', str),
			('label', str),
			('center', dict),
			('size', dict),
		)
	typemap = classmethod(typemap)

class PresetsManagerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('pause time', float),
			('xy only', bool),
			('stage always', bool),
			('cycle', bool),
			('optimize cycle', bool),
			('mag only', bool),
			('apply offset', bool),
			('blank', bool),
			('smallsize', int),
		)
	typemap = classmethod(typemap)

class CorrectorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('instruments', dict),
			('n average', int),
			('camera settings', CameraSettingsData),
			('combine', str),
			('clip min', float),
			('clip max', float),
			('store series', bool),
		)
	typemap = classmethod(typemap)

class NavigatorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('pause time', float),
			('move type', str),
			('check calibration', bool),
			('complete state', bool),
			('override preset', bool),
			('camera settings', CameraSettingsData),
			('instruments', dict),
			('precision', float),
			('accept precision', float),
			('max error', float),
			('cycle each', bool),
			('cycle after', bool),
			('final image shift', bool),
			('background readout', bool),
			('preexpose', bool),
		)
	typemap = classmethod(typemap)

class BakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('bypass', bool),
			('preset', str),
			('total bake time', float),
			('manual aperture', bool),
			('emission off', bool),
		)
	typemap = classmethod(typemap)

class DriftManagerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('threshold', float),
			('pause time', float),
			('camera settings', CameraSettingsData),
			('timeout', int),
		)
	typemap = classmethod(typemap)

class TransformManagerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('registration', str),
			('threshold', float),
			('pause time', float),
			('camera settings', CameraSettingsData),
			('timeout', int),
			('min mag', int),
		)
	typemap = classmethod(typemap)

class FFTMakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process', bool),
			('mask radius', float),
			('label', str),
			('save', bool),
			('reduced', bool),
		)
	typemap = classmethod(typemap)

class FFTAnalyzerSettingsData(SettingsData):
	def typemap(cls):
		return FFTMakerSettingsData.typemap() + (
		)
	typemap = classmethod(typemap)

class FFTAceSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process', bool),
			('label', str),
		)
	typemap = classmethod(typemap)

class TargetFinderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('wait for done', bool),
			('ignore images', bool),
			('queue', bool),
			('user check', bool),
			('queue drift', bool),
			('sort target', bool),
			('allow append', bool),
			('skip', bool),
		)
	typemap = classmethod(typemap)

class ClickTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('no resubmit', bool),
		)
	typemap = classmethod(typemap)

class MatlabTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('test image', str),
			('module path', str),
			('parametergui path', str),
		)
	typemap = classmethod(typemap)

class TestTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('test image', str),
		)
	typemap = classmethod(typemap)

class LowPassFilterSettingsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('on', bool),
			('size', int),
			('sigma', float),
		)
	typemap = classmethod(typemap)

class HoleFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('image filename', str),
			('edge lpf', LowPassFilterSettingsData),
			('edge', bool),
			('edge type', str),
			('edge log size', int),
			('edge log sigma', float),
			('edge absolute', bool),
			('edge threshold', float),
			('template rings', list),
			('template type', str),
			('template lpf', LowPassFilterSettingsData),
			('threshold', float),
			('threshold method', str),
			('blobs border', int),
			('blobs max', int),
			('blobs max size', int),
			('blobs min size', int),
			('lattice spacing', float),
			('lattice tolerance', float),
			('lattice hole radius', float),
			('lattice zero thickness', float),
			('ice min mean', float),
			('ice max mean', float),
			('ice max std', float),
			('focus hole', str),
			('target template', bool),
			('focus template', list),
			('acquisition template', list),
			('focus template thickness', bool),
			('focus stats radius', int),
			('focus min mean thickness', float),
			('focus max mean thickness', float),
			('focus max stdev thickness', float),
			('focus interval', int),
		)
	typemap = classmethod(typemap)

class HoleDepthFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('Hole Untilt filename', str),
			('Hole Tilt filename', str),
			('I filename', str),
			('I0 filename', str),
			('edge lpf', LowPassFilterSettingsData),
			('edge', bool),
			('edge type', str),
			('edge log size', int),
			('edge log sigma', float),
			('edge absolute', bool),
			('edge threshold', float),
			('template rings', list),
			('template type', str),
			('template lpf', LowPassFilterSettingsData),
			('tilt axis', float),
			('threshold', float),
			('blobs border', int),
			('blobs max', int),
			('blobs max size', int),
			('blobs min size', int),
			('pickhole radius', float),
			('pickhole zero thickness', float),
		)
	typemap = classmethod(typemap)

class JAHCFinderSettingsData(HoleFinderSettingsData):
	def typemap(cls):
		return HoleFinderSettingsData.typemap() + (
			('template diameter', int),
			('file diameter', int),
			('template filename', str),
			('template invert', bool),
			('template image min', float),
			('lattice extend', str),
		)
	typemap = classmethod(typemap)

class DTFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('template size', int),
			('correlation lpf', float),
			('correlation type', str),
			('rotate', bool),
			('angle increment', float),
			('snr threshold', float),
		)
	typemap = classmethod(typemap)

class RasterFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('publish polygon', bool),
			('image filename', str),
			('raster preset', str),
			('raster movetype', str),
			('raster overlap', float),
			('raster spacing', int),
			('raster spacing asymm', int),
			('raster angle', float),
			('raster center x', int),
			('raster center y', int),
			('raster center on image', bool),
			('raster limit', int),
			('raster limit asymm', int),
			('raster symmetric', bool),
			('select polygon', bool),
			('ice box size', float),
			('ice thickness', float),
			('ice min mean', float),
			('ice max mean', float),
			('ice max std', float),
			('ice min std', float),
			('focus interval', int),
			('focus convolve', bool),
			('focus convolve template', list),
			('focus constant template', list),
			('focus one', bool),
			('acquisition convolve', bool),
			('acquisition convolve template', list),
			('acquisition constant template', list),
		)
	typemap = classmethod(typemap)

# New node from William Nicholson:
class RasterFCFinderSettingsData(RasterFinderSettingsData):
	def typemap(cls):
		return RasterFinderSettingsData.typemap() + (
		('focus center x', float),
		('focus center y', float),
		('focus radius', float),
		('focus box size', float),
		('focus min mean', float),
		('focus max mean', float),
		('focus min std', float),
		('focus max std', float),
		)
	typemap = classmethod(typemap)

class PolyFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('publish polygon', bool),
			('image filename', str),
			('raster spacing', int),
			('raster angle', float),
			('raster center x', int),
			('raster center y', int),
			('raster center on image', bool),
			('raster limit', int),
			('select polygon', bool),
			('ice box size', float),
			('ice thickness', float),
			('ice min mean', float),
			('ice max mean', float),
			('ice max std', float),
			('focus convolve', bool),
			('focus convolve template', list),
			('focus constant template', list),
			('acquisition convolve', bool),
			('acquisition convolve template', list),
			('acquisition constant template', list),
		)
	typemap = classmethod(typemap)

class RegionFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('image filename', str),
			('min region area', float),
			('max region area', float),
			('ve limit', float),
			('raster spacing', float),
			('raster angle', float),
		)
	typemap = classmethod(typemap)

class BlobFinderSettingsData(Data):
	def typemap(cls):
		return SettingsData.typemap() + (
			('on', bool),
			('border', int),
			('max', int),
			('min size', int),
			('max size', int),
			('min mean', float),
			('max mean', float),
			('min stdev', float),
			('max stdev', float),
		)
	typemap = classmethod(typemap)

class SquareFinderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('lpf', LowPassFilterSettingsData),
			('blobs', BlobFinderSettingsData),
			('threshold', float),
		)
	typemap = classmethod(typemap)

class MosaicClickTargetFinderSettingsData(ClickTargetFinderSettingsData,
																					SquareFinderSettingsData):
	def typemap(cls):
		typemap = ClickTargetFinderSettingsData.typemap()
		typemap += SquareFinderSettingsData.typemap()
		typemap += (
			('calibration parameter', str),
			('scale image', bool),
			('scale size', int),
			('create on tile change', str),
		)
		return typemap
	typemap = classmethod(typemap)

class MosaicSpotFinderSettingsData(ClickTargetFinderSettingsData,
																					SquareFinderSettingsData):
	def typemap(cls):
		typemap = MosaicClickTargetFinderSettingsData.typemap()
		typemap += (
			('autofinder', bool),
		)
		return typemap
	typemap = classmethod(typemap)

class MosaicSectionFinderSettingsData(ClickTargetFinderSettingsData,
																					SquareFinderSettingsData):
	def typemap(cls):
		typemap = MosaicClickTargetFinderSettingsData.typemap()
		typemap += (
			('autofinder', bool),
			('min region area', float),
			('max region area', float),
			('axis ratio', float),
			('ve limit', float),
			('min threshold', float),
			('max threshold', float),
			('find section options', str),
			('section area', float),
			('section axis ratio', float),
			('max sections', int),
			('adjust section area', float),
			('section display', bool),
			('raster spacing', float),
			('raster angle', float),
			('raster preset', str),
			('raster overlap', float),
			('black on white', bool),
		)
		return typemap
	typemap = classmethod(typemap)

class TargetWatcherSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process target type', str),
			('park after list', bool),
			('clear beam path', bool),
		)
	typemap = classmethod(typemap)

class AcquisitionSettingsData(TargetWatcherSettingsData):
	def typemap(cls):
		return TargetWatcherSettingsData.typemap() + (
			('pause time', float),
			('first pause time', float),
			('pause between time', float),
			('move type', str),
			('preset order', list),
			('correct image', bool),
			('display image', bool),
			('save image', bool),
			('wait for process', bool),
			('wait for rejects', bool),
			('wait for reference', bool),
			('wait for transform', bool),
			#('duplicate targets', bool),
			#('duplicate target type', str),
			('wait time', float),
			('iterations', int),
			('adjust for transform', str),
			('use parent mover', bool),
			('drift between', bool),
			('mover', str),
			('move precision', float),
			('accept precision', float),
			('final image shift', bool),
			('save integer', bool),
			('background', bool),
			('use parent tilt', bool),
			('adjust time by tilt', bool),
			('reset tilt', bool),
			('bad stats response', str),
			('bad stats type', str),
			('recheck pause time', int),
			('high mean', float),
			('low mean', float),
			('emission off', bool),
			('target offset row', int),
			('target offset col', int),
			('correct image shift coma', bool),
			('park after target', bool),
		)
	typemap = classmethod(typemap)

class MoverParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('mover', str),
			('move precision', float),
			('accept precision', float),
		)
	typemap = classmethod(typemap)

class BeamTiltImagerSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('beam tilt', float),
			('beam tilt count', int),
			('sites', int),
			('startangle', float),
			('tableau type', str),
			('tableau binning', int),
			('tableau split', int),
			('correlation type', str),
		)
	typemap = classmethod(typemap)

class BeamTiltFixerSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('beam tilt', float),
			('min threshold', float),
			('max threshold', float),
			('correct', bool),
		)
	typemap = classmethod(typemap)

class BeamTiltMeasurementData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('preset', PresetData),
			('target', AcquisitionImageTargetData),
			('beam tilt', dict),
			('mean defocus', float),
			('correction', bool),
		)
	typemap = classmethod(typemap)

class StigAcquisitionSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('stig0x', float),
			('stig0y', float),
			('stig1x', float),
			('stig1y', float),
			('stigcount', int),
			('isdefault', bool),
		)
	typemap = classmethod(typemap)

class FocusSequenceData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('node name', str),
			('sequence', list),
			('isdefault', bool),
		)
	typemap = classmethod(typemap)

class FocusSettingData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('switch', bool),
			('node name', str),
			('name', str),
			('preset name', str),
 			('focus method', str),
			('tilt', float),
			('correlation type', str),
			('fit limit', float),
			('delta min', float),
			('delta max', float),
			('correction type', str),
			('stig correction', bool),
			('stig defocus min', float),
			('stig defocus max', float),
			('check drift', bool),
			('drift threshold', float),
			('reset defocus', bool),
			('isdefault', bool),
		)
	typemap = classmethod(typemap)

class FocuserSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('melt preset', str),
			('melt time', float),
			('acquire final', bool),
			('manual focus preset', str),
			('beam tilt settle time', float),
		)
	typemap = classmethod(typemap)

class AutoExposureSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('mean intensity', float),
			('mean intensity tolerance', float),
			('maximum exposure time', float),
			('maximum attempts', int),
		)
	typemap = classmethod(typemap)

class TiltAcquisitionSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilts', str),
			('use tilts', bool),
			('reset per targetlist', bool),
		)
	typemap = classmethod(typemap)

class TiltAlternaterSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilts', str),
			('use tilts', bool),
			('reset per targetlist', bool),
		)
	typemap = classmethod(typemap)

class CalibratorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('instruments', dict),
			('override preset', bool),
			('camera settings', CameraSettingsData),
			('correlation type', str),
			('lpf sigma', float),
		)
	typemap = classmethod(typemap)

class CalibrationCopierSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('to instruments', dict),
		)
	typemap = classmethod(typemap)

class PixelSizeCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('lattice a', float),
			('lattice b', float),
			('lattice gamma', float),
			('h1', int),
			('k1', int),
			('h2', int),
			('k2', int),
			('distance', float),
		)
	typemap = classmethod(typemap)

class MagCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('minsize', float),
			('maxsize', float),
			('pause', float),
			('label', str),
			('threshold', float),
			('maxcount', int),
			('cutoffpercent', float),
			('minbright', float),
			('maxbright', float),
			('magsteps', int),
		)
	typemap = classmethod(typemap)

class DoseCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('beam diameter', float),
			('scale factor', float),
		)
	typemap = classmethod(typemap)

class BeamSizeCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('beam diameter', float),
		)
	typemap = classmethod(typemap)

class GonModelerSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('measure axis', str),
			('measure points', int),
			('measure interval', float),
			('measure tolerance', float),
			('model axis', str),
			('model magnification', int),
			('model terms', int),
			('model mag only', bool),
			('model tolerance', float),
		)
	typemap = classmethod(typemap)

class BeamTiltCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('defocus beam tilt', float),
			('first defocus', float),
			('second defocus', float),
			('stig beam tilt', float),
			('stig delta', float),
			('measure beam tilt', float),
			('correct tilt', bool),
			('settling time', float),
			('comafree beam tilt', float),
			('comafree misalign', float),
			('imageshift coma tilt', float),
			('imageshift coma step', float),
			('imageshift coma number', int),
			('imageshift coma repeat', int),
		)
	typemap = classmethod(typemap)
		
class MatrixCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		parameters = ['image shift', 'beam shift', 'stage position']
		parameterstypemap = []
		for parameter in parameters:
			parameterstypemap.append(('%s tolerance' % parameter, float))
			parameterstypemap.append(('%s shift fraction' % parameter, float))
			parameterstypemap.append(('%s n average' % parameter, int))
			parameterstypemap.append(('%s interval' % parameter, float))
			parameterstypemap.append(('%s current as base' % parameter, bool))
			parameterstypemap.append(('%s base' % parameter, dict))
		return CalibratorSettingsData.typemap() + tuple(parameterstypemap)
	typemap = classmethod(typemap)

class ImageBeamCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('image shift delta', float),
		)
	typemap = classmethod(typemap)

class ManualAcquisitionSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('camera settings', CameraSettingsData),
			('screen up', bool),
			('screen down', bool),
			('beam blank', bool),
			('correct image', bool),
			('save image', bool),
			('loop pause time', float),
			('image label', str),
			('low dose', bool),
			('low dose pause time', float),
			('defocus1switch', bool),
			('defocus1', float),
			('defocus2switch', bool),
			('defocus2', float),
			('dark', bool),
			('force annotate', bool),
			('reduced params', bool),
		)
	typemap = classmethod(typemap)

class ManualImageLoaderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('instruments', dict),
			('camera settings', CameraSettingsData),
			('save image', bool),
			('tilt group', int),
			('batch script', str),
		)
	typemap = classmethod(typemap)

class IntensityMonitorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('wait time', float),
			('iterations', int),
		)
	typemap = classmethod(typemap)

class RobotSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('column pressure threshold', float),
			('default Z position', float),
			('simulate', bool),
			('turbo on', bool),
			('grid clear wait', bool),
			('pause', bool),
			('grid tray', str),
		)
	typemap = classmethod(typemap)

class GridEntrySettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('grid name', str),
		)
	typemap = classmethod(typemap)

class PlateGridEntrySettingsData(GridEntrySettingsData):
	def typemap(cls):
		return GridEntrySettingsData.typemap() + (
			('plate name', str),
			('grid format name', str),
			('plate format name', str),
		)
	typemap = classmethod(typemap)

class LoggerRecordData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('name', str),
			('levelno', int),
			('levelname', str),
			('pathname', str),
			('filename', str),
			('module', str),
			('lineno', int),
			('created', float),
			('thread', int),
			('process', int),
			('message', str),
			('exc_info', str),
		)
	typemap = classmethod(typemap)

class DoseMeasurementData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('dose', float),
		)
	typemap = classmethod(typemap)

class TomographySettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilt min', float),
			('tilt max', float),
			('tilt start', float),
			('tilt step', float),
			('equally sloped', bool),
			('equally sloped n', int),
			('xcf bin', int),
			('run buffer cycle', bool),
			('align zero loss peak', bool),
			('measure dose', bool),
			('dose', float),
			('min exposure', float),
			('max exposure', float),
			('mean threshold', float),
			('collection threshold', float),
			('tilt pause time', float),
			('measure defocus', bool),
			('integer', bool),
			('intscale', float),
#			('pausegroup', bool),
			('model mag', str),
			('z0 error', float),
			('phi', float),
			('phi2', float),
			('offset', float),
			('offset2', float),
			('z0', float),
			('z02', float),
			('fixed model', bool),
			('use lpf', bool),
#			('use wiener', bool),
			('taper size', int),
			('use tilt', bool),
#			('wiener max tilt', float),
			('fit data points', int),
			('use z0', bool),
			('addon tilts', str),
		)
	typemap = classmethod(typemap)

class TomographySimuSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('simu tilt series', str),
			('model mag', str),
			('z0 error', float),
			('phi', float),
			('phi2', float),
			('offset', float),
			('offset2', float),
			('fixed model', bool),
			('use lpf', bool),
			('taper size', int),
			('use tilt', bool),
			('fit data points', int),
		)
	typemap = classmethod(typemap)

class TomographyPredictionData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('predicted position', dict),
			('predicted shift', dict),
			('position', dict),
			('correlation', dict),
			('correlated position', dict),
			('raw correlation', dict),
			('pixel size', float),
			#('image', TiltSeriesImageData),
			('image', AcquisitionImageData),
			('measured defocus', float),
			('measured fit', float),
		)
	typemap = classmethod(typemap)

class TiltSeriesData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tilt min', float),
			('tilt max', float),
			('tilt start', float),
			('tilt step', float),
			('number', int),
		)
	typemap = classmethod(typemap)

class InternalEnergyShiftData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('before', float),
			('after', float),
		)
	typemap = classmethod(typemap)

class TargetFilterSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('bypass', bool),
			('target type', str),
			('user check', bool),
		)
	typemap = classmethod(typemap)

class TargetRepeaterSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('bypass', bool),
			('reset a', bool),
			('reset z', bool),
			('reset xy', bool),
		)
	typemap = classmethod(typemap)

class TiltRotateSettingsData(TargetRepeaterSettingsData):
	def typemap(cls):
		return TargetRepeaterSettingsData.typemap() + (
			('tilts', str),
		)
	typemap = classmethod(typemap)

class CenterTargetFilterSettingsData(TargetFilterSettingsData):
	def typemap(cls):
		return TargetFilterSettingsData.typemap() + (
			('limit', int),
		)
	typemap = classmethod(typemap)

class SampleTargetFilterSettingsData(TargetFilterSettingsData):
	def typemap(cls):
		return TargetFilterSettingsData.typemap() + (
			('square length', int),
			('bright number', int),
			('dark number', int),
			('median number', int),
		)
	typemap = classmethod(typemap)

class RasterTargetFilterSettingsData(TargetFilterSettingsData):
	def typemap(cls):
		return TargetFilterSettingsData.typemap() + (
			('raster spacing', float),
			('raster angle', float),
			('raster preset', str),
			('raster movetype', str),
			('raster overlap', float),
			('raster offset', bool),
			('ellipse angle', float),
			('ellipse a', float),
			('ellipse b', float),
			('limiting shape', str),
		)
	typemap = classmethod(typemap)

class TiltRasterPatternData(Data):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tilt', int),
			('offset', dict),
		)
	typemap = classmethod(typemap)
	
class TargetRasterPatternData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('target', AcquisitionImageTargetData),
			('pattern', int),
		)
	typemap = classmethod(typemap)
	
class PolygonRasterSettingsData(TargetFilterSettingsData):
	def typemap(cls):
		return TargetFilterSettingsData.typemap() + (
			('spacing', float),
			('angle', float),
		)
	typemap = classmethod(typemap)

class RCTAcquisitionSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilts', str),
			('stepsize', float),
			('pause', float),
			('minsize', float),
			('maxsize', float),
			('medfilt', int),
			('lowfilt', int),
			('drift threshold', float),
			('drift preset', str),
		)
	typemap = classmethod(typemap)

class TiltTrackerSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('activation interval', int),
			('tilts', str),
			('stepsize', float),
			('pause', float),
			('minsize', float),
			('maxsize', float),
			('medfilt', int),
			('lowfilt', float),
			('drift threshold', float),
			('drift preset', str),
		)
	typemap = classmethod(typemap)

class ImageAssessorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('format', str),
			('type', str),
			('image directory', str),
			('outputfile', str),
			('run', str),
			('jump filename', str),
		)
	typemap = classmethod(typemap)

class MaskAssessorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('run', str),
			('mask run', str),
			('jump filename', str),
			('continueon', bool),
		)
	typemap = classmethod(typemap)

class ClickMaskMakerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('preset', str),
			('bin', int),
			('run', str),
			('path', str),
			('jump filename', str),
			('continueon', bool),
		)
	typemap = classmethod(typemap)

class ClickTargetTransformerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('child preset', str),
			('ancestor preset', str),
			('jump filename', str),
		)
	typemap = classmethod(typemap)

class ReferenceSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('bypass', bool),
			('move type', str),
			('pause time', float),
			('interval time', float),
		)
	typemap = classmethod(typemap)

class PresetAdjusterSettingsData(ReferenceSettingsData):
	def typemap(cls):
		return ReferenceSettingsData.typemap() + (
			('override preset', bool),
			('instruments', dict),
			('camera settings', CameraSettingsData),
			('correction presets', list),
			('stage position', dict),
		)
	typemap = classmethod(typemap)

class BeamFixerSettingsData(ReferenceSettingsData):
	def typemap(cls):
		return PresetAdjusterSettingsData.typemap() + (
			('shift step', float),
		)
	typemap = classmethod(typemap)

class ExposureFixerSettingsData(ReferenceSettingsData):
	def typemap(cls):
		return PresetAdjusterSettingsData.typemap() + (
			('required dose', float),
			('adjust method', str),
			('max exposure time', int),
			('max beam diameter', float),
		)
	typemap = classmethod(typemap)

class AlignZLPSettingsData(ReferenceSettingsData):
	def typemap(cls):
		return ReferenceSettingsData.typemap() + (
			('check preset', str),
			('threshold', float),
		)
	typemap = classmethod(typemap)

class TimerData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('node', str),
			('label', str),
			('t', float),
			('t0', TimerData),
			('diff', float),
		)
	typemap = classmethod(typemap)

class StageTiltAxisOffsetData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('offset', float),
		)
	typemap = classmethod(typemap)

class ImageCommentData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('comment', str),
		)
	typemap = classmethod(typemap)

class ImageStatusData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('status', str),
		)
	typemap = classmethod(typemap)

class ImageBackup(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('path', str),
		)
	typemap = classmethod(typemap)

class ImageProcessorSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process', bool),
		)
	typemap = classmethod(typemap)

class ImageProcessDoneData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('status', str),
		)
	typemap = classmethod(typemap)

class DynamicTemplateData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('center_row', float),
			('center_column', float),
			('minsum', float),
			('snr', float),
			('angle', float),
		)
	typemap = classmethod(typemap)

class testtable(Data):
	def typemap(cls):
		return Data.typemap() + (
			('b', int),
			('c', int),
		)
	typemap = classmethod(typemap)

class RaptorProcessorSettingsData(ImageProcessorSettingsData):
	def typemap(cls):
		return ImageProcessorSettingsData.typemap() + (
			('path', str),
			('time', int),
			('binning', int),
		)
	typemap = classmethod(typemap)

class TransformMatrixData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image1', AcquisitionImageData),
			('image2', AcquisitionImageData),
			('matrix', sinedon.newdict.DatabaseArrayType),
		)
	typemap = classmethod(typemap)

class AlignmentTargetList(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('list', ImageTargetListData),
			('label', str),
		)
	typemap = classmethod(typemap)

class AlignmentTargetListDone(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('alignlist', AlignmentTargetList),
		)
	typemap = classmethod(typemap)

class AlignmentManagerSettingsData(TargetRepeaterSettingsData):
	def typemap(cls):
		return TargetRepeaterSettingsData.typemap() + (
			('repeat time', int),
		)
	typemap = classmethod(typemap)

class FixAlignmentData(ReferenceRequestData):
	pass

class ConditioningRequestData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('type', str),
		)
	typemap = classmethod(typemap)

class ConditioningDoneData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('request', ConditioningRequestData),
		)
	typemap = classmethod(typemap)

class ConditionerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('bypass', bool),
			('repeat time', int),
		)
	typemap = classmethod(typemap)

class BufferCyclerSettingsData(ConditionerSettingsData):
	def typemap(cls):
		return ConditionerSettingsData.typemap()
	typemap = classmethod(typemap)

class AutoFillerSettingsData(ConditionerSettingsData):
	def typemap(cls):
		return ConditionerSettingsData.typemap() + (
			('autofiller mode', str),
			('column fill start', float),
			('column fill end', float),
			('loader fill start', float),
			('loader fill end', float),
		)
	typemap = classmethod(typemap)

class DDinfoKeyData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
		)
	typemap = classmethod(typemap)

class DDinfoValueData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('camera', CameraEMData),
			('infokey', DDinfoKeyData),
			('infovalue', str),
		)
	typemap = classmethod(typemap)

class C2ApertureSizeData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tem', InstrumentData),
			('size', int),
		)
	typemap = classmethod(typemap)

class K2FrameDMVersionChangeData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('k2camera', InstrumentData),
			('image', AcquisitionImageData),
			('frame flip', bool),
			('frame rotate', int),
			('dm version', list),
		)
	typemap = classmethod(typemap)

class ProjectionSubModeMappingData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('magnification list', MagnificationsData),
			('name', str),
			('submode index', int),
			('magnification', int),
		)
	typemap = classmethod(typemap)

