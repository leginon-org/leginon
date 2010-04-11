# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $
import math
import presetadjuster
import leginondata
import event
import gui.wx.BeamFixer
from pyami import arraystats

class BeamFixer(presetadjuster.PresetAdjuster):
	# relay measure does events
	eventinputs = presetadjuster.PresetAdjuster.eventinputs + [event.FixBeamEvent]
	eventoutputs = presetadjuster.PresetAdjuster.eventoutputs
	panelclass = gui.wx.BeamFixer.BeamFixerPanel
	settingsclass = leginondata.BeamFixerSettingsData
	defaultsettings = presetadjuster.PresetAdjuster.defaultsettings
	defaultsettings.update({
		'shift step': 25.0,
	})
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.FixBeamEvent]
		presetadjuster.PresetAdjuster.__init__(self, *args, **kwargs)

	def getBeamShiftStep(self):
		#acquire an image to get scope and camera
		camera = self.instrument.getData(leginondata.CameraEMData)
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

	def getAdjustment(self):
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
				state = self.player.state()
				if state == 'stop':
					self.instrument.tem.BeamShift = original_beamshift
					return {}
		# set to the best beam shift
		self.instrument.tem.BeamShift = bestbeamshift
		self.logger.info('Best Beam Shift: %s' % (bestbeamshift,))
		return {'beam shift':bestbeamshift}
