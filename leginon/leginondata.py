# COPYRIGHT:
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org

from leginon import leginonconfig
import sinedon.newdict
import sinedon.data
import os
from pyami import weakattr, fileutil
from leginon import projectdata

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
			('description', str),
			('cs', float),
			('pixelmax', int),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class MagnificationsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('instrument', InstrumentData),
			('projection mode', str),
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

class DigitalCameraData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('ccdcamera', InstrumentData),
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
			('uid', int),
			('gid', int),
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
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class InSessionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', SessionData),
		)
	typemap = classmethod(typemap)

class SessionDoneLog(InSessionData):
	'''
	Mark ending of a session
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('done', bool),
		)
	typemap = classmethod(typemap)

class AutoSessionSetData(Data):
	'''
	Sets of auto grid loader sessions. Such as one cassette in FEI gridloader.
	'''
	def typemap(cls):
		return Data.typemap() + (
			('main launcher', str),
			('base session', SessionData),
		)
	typemap = classmethod(typemap)

class AutoSessionData(InSessionData):
	'''
	Auto grid loader sessions. Including data for startup.
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
			('session set', AutoSessionSetData),
			('slot number', int), # base 1
			('stagez', float),
		)
	typemap = classmethod(typemap)

class AutoTaskData(Data):
	'''
	Workflow to perform on the auto session.
	'''
	def typemap(cls):
		return Data.typemap() + (
			('auto session', AutoSessionData),
			('task', str),
		)
	typemap = classmethod(typemap)

class AutoTaskOrderData(Data):
	'''
	AutoTask running order. The done ones are popped from task order.
	'''
	def typemap(cls):
		return Data.typemap() + (
			('session set', AutoSessionSetData),
			('task order', list),  # taskid sequence for processing
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
	('projection mode', str),
	('magnification', int),
	('spot size', int),
	('intensity', float),
	('image shift', dict),
	('beam shift', dict),
	('diffraction shift', dict),
	('intended defocus', float),
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
	('intensity averaged', bool),
	('inserted', bool),
	('dump', bool),
	('pixel size', dict),
	('energy filtered', bool),
	('energy filter', bool),
	('energy filter width', float),
	('energy filter offset', float),
	('nframes', int),
	('save frames', bool),
	('align frames', bool),
	('tiff frames', bool),
	('eer frames', bool),
	('align filter', str),
	('frames name', str),
	('use frames', tuple),
	('frame time', float),
	('request nframes', int),
	('frame flip', bool),
	('frame rotate', int),
	('temperature', float),
	('temperature status', str),
	('readout delay', int),
	('gain index', int),
	('system corrected', bool), # deprecated in v3.6
	('sum gain corrected', bool),
	('frame gain corrected', bool),
	('system dark subtracted', bool),
	('use cds', bool),
	('fast save', bool),
)

class ScopeEMData(EMData):
	def typemap(cls):
		return EMData.typemap() + scope_params + (
			('tem', InstrumentData),
		)
	typemap = classmethod(typemap)

manacqparams = (
	'projection mode',
	'magnification',
	'spot size',
	'intensity',
	'image shift',
	'diffraction shift',
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
			('beamtilt', dict),
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
			('projection mode', str),
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

class PPBeamTiltRotationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('probe', str),
			('angle', float),		# radians
		)
	typemap = classmethod(typemap)

class PPBeamTiltVectorsData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('probe', str),
			('vectors', tuple),		# pair of vectors, such as [(-1,0),(0,1)]
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

class ImageRotationCalibrationData(BeamProbeDependentCalibrationData):
	def typemap(cls):
		return BeamProbeDependentCalibrationData.typemap() + (
			('rotation', float),
			('comment', str),
		)
	typemap = classmethod(typemap)

class ImageScaleAdditionCalibrationData(BeamProbeDependentCalibrationData):
	def typemap(cls):
		return BeamProbeDependentCalibrationData.typemap() + (
			('scale addition', float),   #fraction above 1 as positive
			('comment', str),
		)
	typemap = classmethod(typemap)

class StageSpeedCalibrationData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tem', InstrumentData),
			('axis', str), # only a axis now
			('slope', float),		# delta-time / speed-in-degrees-per-second
			('intercept', float), # time in seconds
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
			('skip', bool),
			('removed', bool),
			('hasref', bool),
			# tem
			('tem', InstrumentData),
			('projection mode', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('diffraction shift', dict),
			('aperture size', dict),
			('defocus', float),
			('defocus range min', float),
			('defocus range max', float),
			('dose', float),
			('tem energy filter', bool),
			('tem energy filter width', float),
			('probe mode', str),
			# camera
			('ccdcamera', InstrumentData),
			('exposure time', float),
			('dimension', dict),
			('binning', dict),
			('offset', dict),
			('energy filter', bool),
			('energy filter width', float),
			('energy filter offset', float),
			('pre exposure', float),
			('alt channel', bool),
			('save frames', bool),
			('frame time', float),
			('request nframes', int),
			('align frames', bool),
			('align filter', str),
			('use frames', tuple),
			('readout delay', int),
			('fast save', bool),
			('use cds', bool), # K3 only
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
			('projection mode', str),
			('magnification', int),
			('spot size', int),
			('intensity', float),
			('image shift', dict),
			('beam shift', dict),
			('diffraction shift', dict),
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

	def getpath(self, read=True):
		'''return image path for this image. Local cache is first checked if read is True.
			Define environment variable LEGINON_READONLY_IMAGE_PATH and rsync
			the global image path under it.
		'''
		try:
			impath = self['session']['image path']
			impath = leginonconfig.mapPath(impath)
			if read:
				# access cache
				fullname = fileutil.getExistingCacheFile(impath, self.filename())
				if fullname:
					impath = os.path.dirname(fullname)
		except:
			raise
			impath = os.path.abspath(os.path.curdir)
		return impath

	def mkpath(self):
		'''
		create a directory for this image file if it does not exist.
		return the full path of this directory.
		'''
		impath = self.getpath(read=False)
		leginonconfig.mkdirs(impath)
		return impath

	def filename(self):
		if not self['filename']:
			raise RuntimeError('"filename" not set for this image')
		return self['filename'] + '.mrc'

	def imagereadable(self):
		'''
		return boolean.
		'''
		try:
			filepath = os.path.join(self.getpath(),self.filename())
		except:
			# filename not yet set
			return False
		return os.access(filepath, os.F_OK) and os.access(filepath, os.R_OK)

	def imageshape(self):
		'''
		return shape of the image array without reading the mrc file.
		None is returned if no image or mrc file.
		'''
		if self.dbid is None:
			# not yet saved, the array is still in memory
			if self['image'] is not None:
				return self['image'].shape
			else:
				return None
		from pyami import mrc
		try:
			# get shape from mrc header
			filepath = os.path.join(self.getpath(),self.filename())
			h = mrc.readHeaderFromFile(filepath)
			return h['shape'] # (row, col)
		except:
			return None

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
			('denoised', bool), #used to default it to not denoised
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
			('node alias', str),
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
			('phase plate', PhasePlateUsageData),
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
			('square', SquareStatsData), # one target may be on multiple ptolemy squares
			('ptolemy_hole', PtolemyHoleData), # multiple target may be from on ptolemy hole
		)
	typemap = classmethod(typemap)

class ReferenceTargetData(ImageTargetData):
	def typemap(cls):
		return ImageTargetData.typemap() + (
			('image', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class TargetOrderData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('list', ImageTargetListData),
			('order', tuple), #tuple of target number, i,e, (1,2,5,4,3)
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

class PhasePlateLogData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tem', InstrumentData),
			('phase plate number', int),
			('patch position', int),
		)
	typemap = classmethod(typemap)

class PhasePlatePatchStateData(PhasePlateLogData):
	def typemap(cls):
		return PhasePlateLogData.typemap() + (
			('bad', bool),
		)
	typemap = classmethod(typemap)

class PhasePlateTestLogData(PhasePlateLogData):
	def typemap(cls):
		return PhasePlateLogData.typemap() + (
			('image', AcquisitionImageData),
			('test type', str),
		)
	typemap = classmethod(typemap)

class PhasePlateUsageData(PhasePlateLogData):
	def typemap(cls):
		return PhasePlateLogData.typemap()
	typemap = classmethod(typemap)

class MeasureDoseData(ReferenceRequestData):
	pass

class PhasePlateData(ReferenceRequestData):
	pass

class AdjustPresetData(ReferenceRequestData):
	pass

class FixBeamData(AdjustPresetData):
	pass

class ScreenCurrentLoggerData(ReferenceRequestData):
	pass

class ScreenCurrentData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('reference', ReferenceTargetData),
			('preset', PresetData),
			('current', float),
		)
	typemap = classmethod(typemap)

class ImageTargetListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('label', str),
			('mosaic', bool),
			('image', AcquisitionImageData),
			('queue', QueueData),
			('sublist', bool),
			('node', NodeSpecData),
		)
	typemap = classmethod(typemap)
	

class TomoTargetOffsetData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('list', ImageTargetListData),
			('focusoffset', tuple),
			('trackoffset', tuple),
			#('trackpreset', str),
		)
	typemap = classmethod(typemap)

class GroupData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('description', str),
			('privilege', projectdata.privileges),
		)
	typemap = classmethod(typemap)


class DequeuedImageTargetListData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('queue', QueueData),
			('list', ImageTargetListData),
		)
	typemap = classmethod(typemap)

class DoneImageTargetListData(InSessionData):
	'''
	TODO: This may replace DequeuedImageTargetListData since
	ImageTargetListData now have NodeSpecData reference.
	'''
	def typemap(cls):
		return InSessionData.typemap() + (
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
			('diffraction shift', dict),
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

class IceTargetFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', AcquisitionImageData),
			('user-check', bool),
			('skip-auto', bool),
			('queue', bool),
			('stats-radius', float),
			('ice-zero-thickness', float),
			('ice-min-thickness', float),
			('ice-max-thickness', float),
			('ice-max-stdev', float),
			('ice-min-stdev', float),
			('template-on', bool),
			('template-focus', tuple),
			('template-acquisition', tuple),
			('filter-ice-on-convolved-on', bool),
			('sampling targets', bool),
			('max sampling', int),
			('randomize acquisition',bool),
			('random y offset',int),
			('randomize chunky',bool),
		)
	typemap = classmethod(typemap)

class HoleFinderPrefsData(IceTargetFinderPrefsData):
	def typemap(cls):
		return IceTargetFinderPrefsData.typemap() + (
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
			('template-diameter', int),
			('file-diameter', int),
			('template-filename', str),
			('dog-diameter', int),
			('dog-invert', bool),
			('dog-k-factor', float),
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
			('finder-type', str),
			('prefs', HoleFinderPrefsData),
			('score-prefs', ScoreTargetFinderPrefsData),
			('row', int),
			('column', int),
			('mean', float),
			('stdev', float),
			('thickness-mean', float),
			('thickness-stdev', float),
			('good', bool),
			('score', float),
			('hole-number', int),
			('convolved', bool),
			('ptolemy', PtolemyHoleData),
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

class ScoreSquareFinderPrefsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('image', MosaicImageData),
			('filter-min', float),
			('filter-max', float),
			('filter-key', str),
		)
	typemap = classmethod(typemap)

class PtolemySquareData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('grid_id', int), #ImageListData.dbid
			('tile_id', int), #AcquisitionImageData.dbid of the mosaic tile
			('square_id', int), #assigned by ptolemy
			('center_x', int),
			('center_y', int),
		)
	typemap = classmethod(typemap)

class PtolemyScoreHistoryData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('list', ImageTargetListData), #where the ptolemy square is from.
			('square', PtolemySquareData),
			('score', float),
			('set_number', int),
		)
	typemap = classmethod(typemap)
		
class PtolemyHoleData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('square', PtolemySquareData),
			('image', AcquisitionImageData),
			('hole_id', int), #
			('center_x', int),
			('center_y', int),
		)
	typemap = classmethod(typemap)

class SquareStatsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('prefs', SquareFinderPrefsData),
			('score_prefs', ScoreSquareFinderPrefsData),
			('tile_image', AcquisitionImageData),
			('row', int),
			('column', int),
			('size', float),
			('mean', float),
			('stdev', float),
			('score', float),
			('good', bool),
			('on_edge', bool),
		)
	typemap = classmethod(typemap)

class PtolemySquareStatsLinkData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('ptolemy', PtolemySquareData),
			('stats', SquareStatsData),
		)
	typemap = classmethod(typemap)

class SettingsData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('name', str),
			('isdefault', bool),
		)
	typemap = classmethod(typemap)

class ClientPortData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('hostname', str),
			('primary port', int),
			('send port start', int),
			('send port end', int),
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
			('request nframes', int),
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
			('alpha tilt', float),
			('use spiral path', bool),
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
			('pause time', float), # seconds
			('xy only', bool),
			('stage always', bool),
			('cycle', bool),
			('optimize cycle', bool),
			('import random', bool),
			('mag only', bool),
			('apply offset', bool),
			('disable stage for image shift', bool),
			('blank', bool),
			('smallsize', int),
			('idle minute', float), # minutes
			('emission off', bool),
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
			('beam tilt', float),
			('camera settings', CameraSettingsData),
			('timeout', int),
			('measure drift interval', int),
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
			('check method', str),
			('queue drift', bool),
			('sort target', bool),
			('allow append', bool),
			('multifocus', bool),
			('skip', bool),
			('allow no focus', bool),
			('allow no acquisition', bool),
		)
	typemap = classmethod(typemap)

class ClickTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('no resubmit', bool),
		)
	typemap = classmethod(typemap)

class TomoClickTargetFinderSettingsData(ClickTargetFinderSettingsData):
	def typemap(cls):
		return ClickTargetFinderSettingsData.typemap() + (
			('auto focus target', bool),
			('focus target offset', float),
			('track target offset', float),
			('tomo beam diameter', float),
			('focus beam diameter', float),
			('track beam diameter', float),
			('stretch tomo beam', bool),
			('stretch focus beam', bool),
			('stretch track beam', bool),
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

class StitchTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('test image', str),
			('overlap', float),
			('coverage', float),
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

class IceTargetFinderSettingsData(TargetFinderSettingsData):
	def typemap(cls):
		return TargetFinderSettingsData.typemap() + (
			('lattice hole radius', float),
			('lattice zero thickness', float),
			('ice min mean', float),
			('ice max mean', float),
			('ice max std', float),
			('ice min std', float),
			('focus hole', str),
			('target template', bool),
			('focus template', list),
			('acquisition template', list),
			('focus template thickness', bool),
			('focus stats radius', int),
			('focus min mean thickness', float),
			('focus max mean thickness', float),
			('focus min stdev thickness', float),
			('focus max stdev thickness', float),
			('focus interval', int),
			('focus offset row', int),
			('focus offset col', int),
			('filter ice on convolved', bool),
			('sampling targets', bool),
			('max sampling', int),
			('randomize acquisition',bool),
			('random y offset',int),
			('randomize chunky',bool),
		)
	typemap = classmethod(typemap)

class PtolemyMmTargetFinderSettingsData(IceTargetFinderSettingsData):
	def typemap(cls):
		return IceTargetFinderSettingsData.typemap() + (
			('score key', str),
			('score threshold', float),
		)
	typemap = classmethod(typemap)

class ScoreTargetFinderSettingsData(IceTargetFinderSettingsData):
	def typemap(cls):
		return IceTargetFinderSettingsData.typemap() + (
			('script', str),
			('score key', str),
			('score threshold', float),
		)
	typemap = classmethod(typemap)

class ScoreTargetFinderPrefsData(IceTargetFinderPrefsData):
	def typemap(cls):
		return IceTargetFinderPrefsData.typemap() + (
			('script', str),
			('score-key', str),
			('score-threshold', float),
		)
	typemap = classmethod(typemap)

class TemplateTargetFinderSettingsData(IceTargetFinderSettingsData):
	def typemap(cls):
		return IceTargetFinderSettingsData.typemap() + (
			('image filename', str),
			('template type', str),
			('template lpf', LowPassFilterSettingsData),
			('threshold', float),
			('threshold method', str),
			('blobs border', int),
			('blobs max', int),
			('blobs max size', int),
			('blobs min size', int),
			('blobs min roundness', float),
			('lattice spacing', float),
			('lattice tolerance', float),
		)
	typemap = classmethod(typemap)

class JAHCFinderSettingsData(TemplateTargetFinderSettingsData):
	def typemap(cls):
		return TemplateTargetFinderSettingsData.typemap() + (
			('template diameter', int),
			('file diameter', int),
			('template filename', str),
			('template invert', bool),
			('template image min', float),
			('lattice extend', str),
			('template multiple', int),
			('multihole angle', float),
			('multihole spacing', float),
		)
	typemap = classmethod(typemap)

class HoleFinderSettingsData(JAHCFinderSettingsData):
	def typemap(cls):
		return JAHCFinderSettingsData.typemap() + (
			('edge lpf', LowPassFilterSettingsData),
			('edge', bool),
			('edge type', str),
			('edge log size', int),
			('edge log sigma', float),
			('edge absolute', bool),
			('edge threshold', float),
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

class ExtHoleFinderSettingsData(TemplateTargetFinderSettingsData):
	def typemap(cls):
		return TemplateTargetFinderSettingsData.typemap() + (
			('hole diameter', int),
			('command', str),
		)
	typemap = classmethod(typemap)

class DoGFinderSettingsData(HoleFinderSettingsData):
	def typemap(cls):
		return HoleFinderSettingsData.typemap() + (
			('dog diameter', int),
			('dog invert', bool),
			('dog k-factor', float),
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
		return IceTargetFinderSettingsData.typemap() + (
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

class BlobFinderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('on', bool),
			('border', int),
			('max', int),
			('min size', int), # rough cutoff in blob finding
			('max size', int), # rough cutoff in blob finding
			('min mean', float),
			('max mean', float),
			('min stdev', float),
			('max stdev', float),
			('min filter size', int), # filter for targets
			('max filter size', int), # filter for targets
		)
	typemap = classmethod(typemap)

class TargetGroupingSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('total targets', int),
			('classes', int),
			('group method', str),
			('randomize blobs', bool),
		)
	typemap = classmethod(typemap)

class SquareFinderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('lpf', LowPassFilterSettingsData),
			('blobs', BlobFinderSettingsData),
			('target grouping', TargetGroupingSettingsData),
			('target multiple', int),
			('threshold', float),
		)
	typemap = classmethod(typemap)

class TopScoreFinderSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('target grouping', TargetGroupingSettingsData),
			('target multiple', int),
			('filter-min', float),
			('filter-max', float),
			('filter-key', str),
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
			('autofinder', bool),
		)
		return typemap
	typemap = classmethod(typemap)

class MosaicScoreTargetFinderSettingsData(ClickTargetFinderSettingsData,
																					TopScoreFinderSettingsData):
	def typemap(cls):
		typemap = ClickTargetFinderSettingsData.typemap()
		typemap += TopScoreFinderSettingsData.typemap()
		typemap += (
			('scoring script', str),
			('calibration parameter', str),
			('scale image', bool),
			('scale size', int),
			('create on tile change', str),
			('autofinder', bool),
			('simpleblobmerge', bool),
		)
		return typemap
	typemap = classmethod(typemap)

class MosaicLearnTargetFinderSettingsData(ClickTargetFinderSettingsData,
																					TopScoreFinderSettingsData):
	def typemap(cls):
		typemap = ClickTargetFinderSettingsData.typemap()
		typemap += TopScoreFinderSettingsData.typemap()
		typemap += (
			('calibration parameter', str),
			('scale image', bool),
			('scale size', int),
			('create on tile change', str),
			('autofinder', bool),
			('simpleblobmerge', bool),
		)
		return typemap
	typemap = classmethod(typemap)
class MosaicSpotFinderSettingsData(ClickTargetFinderSettingsData,
																					SquareFinderSettingsData):
	def typemap(cls):
		typemap = MosaicClickTargetFinderSettingsData.typemap()
		return typemap
	typemap = classmethod(typemap)

class MosaicSectionFinderSettingsData(ClickTargetFinderSettingsData,
																					SquareFinderSettingsData):
	def typemap(cls):
		typemap = MosaicClickTargetFinderSettingsData.typemap()
		typemap += (
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

class MosaicQuiltFinderSettingsData(JAHCFinderSettingsData):
	def typemap(cls):
		typemap = JAHCFinderSettingsData.typemap()
		typemap += (
			('calibration parameter', str),
			('scale image', bool),
			('scale size', int),
			('create on tile change', str),
			('no resubmit', bool),
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
	
class TargetMapHandlerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process target type', str),
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
			#('duplicate targets', bool),
			#('duplicate target type', str),
			('loop delay time', float),
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
			('reacquire when failed', bool),
			('recheck pause time', int),
			('high mean', float),
			('low mean', float),
			('target offset row', int),
			('target offset col', int),
			('correct image shift coma', bool),
			('park after target', bool),
			('set aperture', bool),
			('objective aperture',str),
			('c2 aperture',str),
			('limit image',bool),
			('limit preset',str),
			('limit number',int),
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
			('do auto coma', bool),
			('auto coma limit', float),
			('auto coma count limit', int),
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
			('recheck drift', bool),
			('drift threshold', float),
			('reset defocus', bool),
			('isdefault', bool),
		)
	typemap = classmethod(typemap)

class SingleFocuserSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('melt preset', str),
			('melt time', float),
			('acquire final', bool),
			('manual focus preset', str),
			('beam tilt settle time', float),
			('on phase plate', bool),
			('accuracy limit', float),
		)
	typemap = classmethod(typemap)

class FocuserSettingsData(SingleFocuserSettingsData):
	def typemap(cls):
		return SingleFocuserSettingsData.typemap()
	typemap = classmethod(typemap)

class DiffrFocuserSettingsData(FocuserSettingsData):
	def typemap(cls):
		return FocuserSettingsData.typemap() + (
			('tilt start', float), # degrees
			('tilt range', float), # degrees
			('tilt speed', float), # degrees per second
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

class TiltAlternaterSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilts', str), # Issue #5687. should be tuple. Too late now.
			('use tilts', bool),
			('reset per targetlist', bool),
		)
	typemap = classmethod(typemap)

class TiltListAlternaterSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('tilts', str), # Issue #5687. should be tuple, Too late now.
			('use tilts', bool),
		)
	typemap = classmethod(typemap)

class MoveAcquisitionSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('acquire during move', bool),
			('imaging delay', float),  #seconds
			('move to', list),		#list of degrees or (x,y) tuple in um
			('total move time', float),  #seconds
		)
	typemap = classmethod(typemap)

class MoveXYAcquisitionSettingsData(MoveAcquisitionSettingsData):
	def typemap(cls):
		return MoveAcquisitionSettingsData.typemap() # "move to" is list of tuple
	typemap = classmethod(typemap)

class MoveAlphaAcquisitionSettingsData(MoveAcquisitionSettingsData):
	def typemap(cls):
		return MoveAcquisitionSettingsData.typemap() + (
			('tilt to', float),		#degrees
			('nsteps', int),
		)
	typemap = classmethod(typemap)

class DefocusSequenceSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('step size', float),  #meter
			('nsteps', int),
		)
	typemap = classmethod(typemap)

class BatchAcquisitionSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('shutter delay', float),  #seconds
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

class ScaleRotationCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap()
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
		parameters = ['image shift', 'beam shift', 'diffraction shift', 'stage position']
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
			('max loop', int),
			('image label', str),
			('low dose', bool),
			('low dose pause time', float),
			('defocus1switch', bool),
			('defocus1', float),
			('defocus2switch', bool),
			('defocus2', float),
			('do defocus series', bool),
			('defocus start', float),
			('defocus step', float),
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
			('stage z', float),
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
			('tilt order', str),
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
			('disable backlash correction', bool),
			('tilt pause time', float),
			('backlash pause time', float),
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
			('fit data points2', int),
			('use z0', bool),
			('addon tilts', str),
			('use preset exposure', bool),
		)
	typemap = classmethod(typemap)

class Tomography2SettingsData(TomographySettingsData):
	def typemap(cls):
		return TomographySettingsData.typemap() + (
			('track preset', str),
			('cosine dose', bool),
			('full track', bool),
			('tolerance', float),
			('maxfitpoints', int),
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
			('tilt group', int),
		)
	typemap = classmethod(typemap)

class TiltDefocusCalibrationData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tem', InstrumentData),
			('reference tilt', float), #radians
			('tilts', tuple), #sorted, in radians
			('defocus deltas', tuple), # matching defocus in meters
		)
	typemap = classmethod(typemap)

class TiltSeriesData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tilt min', float),
			('tilt max', float),
			('tilt start', float),
			('tilt step', float),
			('tilt order', str),
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
			('return settle time', float),
			('mover', str),
			('move precision', float),
			('accept precision', float),
		)
	typemap = classmethod(typemap)

class ReferenceTimerSettingsData(ReferenceSettingsData):
	def typemap(cls):
		return ReferenceSettingsData.typemap() + (
			('interval time', float),
		)
	typemap = classmethod(typemap)

class ReferenceCounterSettingsData(ReferenceSettingsData):
	def typemap(cls):
		return ReferenceSettingsData.typemap() + (
			('interval count', int),
		)
	typemap = classmethod(typemap)

class PresetAdjusterSettingsData(ReferenceTimerSettingsData):
	def typemap(cls):
		return ReferenceTimerSettingsData.typemap() + (
			('override preset', bool),
			('instruments', dict),
			('camera settings', CameraSettingsData),
			('correction presets', list),
			('stage position', dict),
		)
	typemap = classmethod(typemap)

class BeamFixerSettingsData(ReferenceTimerSettingsData):
	def typemap(cls):
		return PresetAdjusterSettingsData.typemap() + (
			('shift step', float),
		)
	typemap = classmethod(typemap)

class ExposureFixerSettingsData(ReferenceTimerSettingsData):
	def typemap(cls):
		return PresetAdjusterSettingsData.typemap() + (
			('required dose', float),
			('adjust method', str),
			('max exposure time', int),
			('max beam diameter', float),
		)
	typemap = classmethod(typemap)

class AlignZLPSettingsData(ReferenceTimerSettingsData):
	def typemap(cls):
		return ReferenceTimerSettingsData.typemap() + (
			('check preset', str),
			('threshold', float),
		)
	typemap = classmethod(typemap)

class PhasePlateAlignerSettingsData(ReferenceTimerSettingsData):
	def typemap(cls):
		return ReferenceCounterSettingsData.typemap() + (
			('phase plate number', int),
			('total positions', int),
			('initial position', int),
			('settle time', float),
			('charge time', float),
			('tilt charge time', float),
			('tilt charge angle', float),
		)
	typemap = classmethod(typemap)

class PhasePlateTestImagerSettingsData(AcquisitionSettingsData):
	def typemap(cls):
		return AcquisitionSettingsData.typemap() + (
			('phase plate number', int),
		)
	typemap = classmethod(typemap)

class PhasePlateTesterSettingsData(PhasePlateTestImagerSettingsData):
	def typemap(cls):
		return PhasePlateTestImagerSettingsData.typemap() + (
			('total positions', int),
			('start position', int),
			('current position', int),
			('total test positions', int),
		)
	typemap = classmethod(typemap)

class ScreenCurrentLoggerSettingsData(ReferenceTimerSettingsData):
	def typemap(cls):
		return ReferenceTimerSettingsData.typemap()
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

class MosaicTransformMatrixData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('imagelist1', ImageListData),
			('imagelist2', ImageListData),
			('matrix', sinedon.newdict.DatabaseArrayType),
			('move type', str),
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
			('repeat time', int), # seconds
		)
	typemap = classmethod(typemap)

class BufferCyclerSettingsData(ConditionerSettingsData):
	def typemap(cls):
		return ConditionerSettingsData.typemap() + (
			('trip value', float),
		)
	typemap = classmethod(typemap)

class ColdFegFlasherSettingsData(ConditionerSettingsData):
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
			('delay dark current ref', int),
			('start dark current ref hr', int),
			('end dark current ref hr', int),
			('extra dark current ref', bool),
			('dark current ref repeat time', int), # seconds
		)
	typemap = classmethod(typemap)

class TEMControllerSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('retract obj ap on grid changing', bool),
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

class DDTransferData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('image', AcquisitionImageData),
			('framename', str),
			('cameraparamsfile', str),
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

class BufferHostData(DigitalCameraData):
	def typemap(cls):
		return DigitalCameraData.typemap() + (
			('buffer hostname', str),
			('buffer base path', str),
			('disabled', bool),
			('append full head', bool),
		)
	typemap = classmethod(typemap)

class BufferFramePathData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('host', BufferHostData),
			('buffer frame path', str),
		)
	typemap = classmethod(typemap)

class CameraDarkCurrentUpdatedData(Data):
	'''
	Log camera software update of dark current reference.
	'''
	def typemap(cls):
		return Data.typemap() + (
			('hostname', str),
		)
	typemap = classmethod(typemap)

class ZeroLossIceThicknessData(InSessionData):
	def typemap(cls):
		return Data.typemap() + (
			('image', AcquisitionImageData),
			('slit mean', float),
			('slit sd', float),
			('no slit mean', float),
			('no slit sd', float),
			('thickness', float),
		)
	typemap = classmethod(typemap)

class ObjIceThicknessData(InSessionData):
	def typemap(cls):
		return Data.typemap() + (
			('image', AcquisitionImageData),
			('vacuum intensity', float),
			('mfp', float),
			('intensity', float),
			('thickness', float),
		)
	typemap = classmethod(typemap)


class ZeroLossIceThicknessSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process', bool),
			('exposure time', float),
			('slit width', float),
			('mean free path', float),   #nm
			('decimate', int),
			('binning', int),
			('process_obj_thickness', bool),
			('obj mean free path', float),
			('vacuum intensity', float),
			('use_best_quart_stats', bool),
			('cfeg',bool),
			('cfeg_slope',float),
			('cfeg_intercept',float),
		)
	typemap = classmethod(typemap)

class BlackStripeSettingsData(SettingsData):
	def typemap(cls):
		return SettingsData.typemap() + (
			('process', bool),
			('pause', bool),
		)
	typemap = classmethod(typemap)

class DiffractionSeriesData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('tilt start', float),
			('tilt range', float),
			('tilt speed', float),
			('parent', AcquisitionImageData),
			('preset', PresetData),
			('emtarget', EMTargetData),
			('series length', int),
		)
	typemap = classmethod(typemap)

class DeletedDiffractionSeriesData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('series', DiffractionSeriesData),
			('comment', str),
		)
	typemap = classmethod(typemap)

class CameraLengthCalibrationData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('magnification', int),
			('camera length', float), #meters
			('comment', str),
		)
	typemap = classmethod(typemap)

class CameraLengthCalibratorSettingsData(CalibratorSettingsData):
	def typemap(cls):
		return CalibratorSettingsData.typemap() + (
			('d spacing', float),
			('distance', float),
		)
	typemap = classmethod(typemap)

class BeamstopCenterData(CalibrationData):
	def typemap(cls):
		return CalibrationData.typemap() + (
			('beam center', dict), # mm as defined in smv file header
		)
	typemap = classmethod(typemap)

#------EPU upload---------
class EpuData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('name', str),
			('preset name', str),
			('datetime_string', str),
			('version', int),
			('image', AcquisitionImageData),
			('parent', EpuData),
		)
	typemap = classmethod(typemap)

class EpuMatrixData(InSessionData):
	def typemap(cls):
		return InSessionData.typemap() + (
			('matrix', sinedon.newdict.DatabaseArrayType),
			('preset name', str),
			('magnification', int),
		)
	typemap = classmethod(typemap)
