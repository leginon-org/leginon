# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $
import math
import reference
import leginondata
import event
import gui.wx.BeamFixer
from pyami import arraystats

class BeamFixer(reference.Reference):
	# relay measure does events
	eventinputs = reference.Reference.eventinputs + [event.FixBeamEvent]
	eventoutputs = reference.Reference.eventoutputs + [event.UpdatePresetEvent]
	panelclass = gui.wx.BeamFixer.BeamFixerPanel
	settingsclass = leginondata.BeamFixerSettingsData
	defaultsettings = reference.Reference.defaultsettings
	defaultsettings.update({
		'override preset': False,
		'instruments': {'tem':None, 'ccdcamera':None},
		'camera settings':
			leginondata.CameraSettingsData(
				initializer={
					'dimension': {
						'x': 1024,
						'y': 1024,
					},
					'offset': {
						'x': 0,
						'y': 0,
					},
					'binning': {
						'x': 1,
						'y': 1,
					},
					'exposure time': 200.0,
				}
			),
		'shift step': 25.0,
		'correction presets': [],
	})
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.FixBeamEvent]
		reference.Reference.__init__(self, *args, **kwargs)

	def processData(self, incoming_data):
		reference.Reference.processData(self, incoming_data)
		if isinstance(incoming_data, leginondata.FixBeamData):
			newdata = incoming_data.toDict()
			newdata['preset'] = self.settings['correction presets'][0]
			self.processRequest(newdata)

	def acquire(self):
		if self.settings['override preset']:
			## use override
			instruments = self.settings['instruments']
			try:
				self.instrument.setTEM(instruments['tem'])
				self.instrument.setCCDCamera(instruments['ccdcamera'])
			except ValueError, e:
				self.logger.error('Cannot set instruments: %s' % (e,))
				return
			try:
				self.instrument.ccdcamera.Settings = self.settings['camera settings']
			except Exception, e:
				errstr = 'Acquire image failed: %s'
				self.logger.error(errstr % e)
				return
		else:
			# default to current camera config set by preset
			if self.presets_client.getCurrentPreset() is None:
				self.logger.error('Preset is unknown and preset override is off')
				return
		return self._acquire()

	def _acquire(self):
		try:
			imagedata = self.instrument.getData(leginondata.CorrectedCameraImageData)
		except:
			self.logger.error('unable to get corrected image')
			return
		return imagedata

	def getBeamShiftStep(self):
		#acquire an image to get scope and camera
		camera = self.instrument.getData(leginondata.CameraEMData, image=False)
		scope = self.instrument.getData(leginondata.ScopeEMData)
		beamshiftcal = self.calibration_clients['beam shift']
		shiftstep = 0.01 * self.settings['shift step']
		camdimension = camera['dimension']
		pixelshift = {}
		pixelshift['col'] = camdimension['x'] * shiftstep
		pixelshift['row'] = camdimension['y'] * shiftstep
		try:
			scope2 = beamshiftcal.transform(pixelshift,scope,camera)
			shiftx = scope2['beam shift']['x'] - scope['beam shift']['x']
			shifty = scope2['beam shift']['y'] - scope['beam shift']['y']
			beamshift = {'x': shiftx, 'y': shifty}
		except Exception, e:
			self.logger.warning(e)
			beamshift = {'x':1e-07, 'y':1e-07}
		beamshiftlength = math.sqrt(beamshift['x']**2 + beamshift['y']**2)
		self.logger.info('Calculated Beam Shift Step: %s' %(beamshiftlength))
		return beamshiftlength

	def execute(self, request_data=None):
		# get current beam shift
		original_beamshift = self.instrument.tem.BeamShift
		bestbeamshift = original_beamshift
		maxvalue = 0
		step = self.getBeamShiftStep()
		for beamx in (-step, 0,step):
			newbeamx = original_beamshift['x'] + beamx
			for beamy in (-step, 0,step):
				newbeamy = original_beamshift['y'] + beamy

				# set scope parameters
				newbeamshift = {'x': newbeamx, 'y': newbeamy}
				self.instrument.tem.BeamShift = newbeamshift
				self.logger.info('change beam shift to: %s' %(newbeamshift))

				# acquire image
				imagedata = self.acquire()
				if imagedata is None:
					self.logger.error('Failed to Fix Beam Shift')
					return
				# check image
				image = imagedata['image']
				self.setImage(image, 'Image')
				meanvalue = arraystats.mean(image)
				if meanvalue > maxvalue:
					maxvalue = meanvalue
					bestbeamshift = newbeamshift
		# set to the best beam shift
		self.instrument.tem.BeamShift = bestbeamshift
		self.logger.info('Best Beam Shift: %s' % (bestbeamshift,))
		# update the preset beam shift
		correction_presets = self.settings['correction presets']
		if request_data:
			if request_data['preset'] not in correction_presets:
				correction_presets.append(request_data['preset'])
			for presetname in correction_presets:
				params = {'beam shift':bestbeamshift}
				self.presets_client.updatePreset(presetname, params)
