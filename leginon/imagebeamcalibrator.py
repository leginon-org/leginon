#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import event, leginondata
from pyami import correlator, peakfinder
import sys
import time
import calibrationclient
import threading
import node
import gui.wx.ImageBeamCalibrator
import numpy

class CalibrationError(Exception):
	pass

class Aborted(Exception):
	pass

class ImageBeamCalibrator(calibrator.Calibrator):
	'''
	Calibrates beam shift required for compensate image shift.
	'''
	panelclass = gui.wx.ImageBeamCalibrator.Panel
	settingsclass = leginondata.ImageBeamCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'image shift delta': 2e-6,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)

		self.parameters = {
		  'image shift': calibrationclient.ImageShiftCalibrationClient(self),
		  'beam shift': calibrationclient.BeamShiftCalibrationClient(self),
		}
		self.parameter = 'beam shift'
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.settle = {
		  'image shift': 5.0,
		  'beam shift': 1.0,
		}

		self.axislist = ['x', 'y']
		self.aborted = threading.Event()

		self.start()

	def calibrate(self):
		'''
		The initialization of interactive calibration
		'''
		if self.initInstruments():
			# has error when initialize instruments
			self.instrument_status = 'bad'
			return
		self.aborted.clear()
		mag, mags = self.getMagnification()
		pixsize = self.pixsizeclient.retrievePixelSize(None, None, mag)

		cam = self.instrument.ccdcamera

		self.image_pixelshifts = []
		self.beam_positionshifts = []
		self.axismap = {'x':0,'y':1}

	def getBaseImageBeamShift(self):
		# This gives base for both beam shift and image shift to return to
		self.parameter = 'beam shift'
		self.beambase = self.getParameter()
		self.parameter = 'image shift'
		self.imagebase = self.getParameter()

	def moveImage(self,axis):
		i = self.axismap[axis]
		# get pixel shift by image shift
		delta = self.settings['image shift delta']
		self.logger.debug('Delta %s' % delta)
		self.parameter = 'image shift'
		calclient = self.parameters[self.parameter]
		position = self.getParameter()
		position[axis] += delta
		calclient = self.parameters[self.parameter]
		self.scope,self.camera = self.getCurrentScopeCameraEMData()
		# shift in pixel for the camera config
		shift = calclient.itransform(position, self.scope, self.camera)
		# pixelshift beam has to move is in the opposite direction
		rowpix = -shift['row']
		colpix = -shift['col']
		self.image_pixelshifts.append((rowpix,colpix))

		### set image shift
		basevalue = self.imagebase[axis]
		newvalue = basevalue + delta
		self.logger.debug('New value %s' % newvalue)

		state1 = self.makeState(basevalue, axis)
		state2 = self.makeState(newvalue, axis)
		self.instrument.tem.ImageShift = state2
		self.logger.debug('States %s, %s' % (state1, state2))

		self.logger.info('Shift between images: (%.2f, %.2f)' % (colpix, rowpix))

	def getBeamState(self,axis):
		newbeamstate = self.instrument.tem.BeamShift
		#simulator test
		tem_name = self.instrument.getTEMName()
		if 'Sim' in tem_name:
			self.logger.info('fake beam shift in simulator')
			if axis == 'x':
				newbeamstate['x'] = 1.8e-6
				newbeamstate['y'] = -6.7e-7
			elif axis == 'y':
				newbeamstate['x'] = -6.3e-7
				newbeamstate['y'] = -1.9e-6
		self.logger.info('got new state')
		return newbeamstate

	def saveBeamShift(self,axis):	
		i = self.axismap[axis]
		self.parameter = 'beam shift'

		newbeamstate = self.getBeamState(axis)

		if newbeamstate == self.beambase:
			self.logger.error('Calibration Failed: Change in %s is zero' % self.parameter)
			self.uiAbort()
		beamchange = {'x':newbeamstate['x']-self.beambase['x'],'y':newbeamstate['y']-self.beambase['y']}
		self.logger.info('scope %s axis % s change : (x,y)=(%s,%s)' % (self.parameter,axis,beamchange['x'],beamchange['y']))

		self.beam_positionshifts.append(beamchange)

	def returnToBase(self):
		try:
			# return to base
			self.logger.info('Returning to original state')
			emdata = leginondata.ScopeEMData()
			emdata['image shift'] = self.imagebase
			emdata['beam shift'] = self.beambase
			self.instrument.setData(emdata)
		except Exception, e:
			self.logger.exception('Could not return to original state: %s', e)
			self.panel.calibrationDone()


	def calculateMatrix(self):
		mag, mags = self.getMagnification()
		ht = self.getHighTension()
	
		self.parameter = 'beam shift'
		calclient = self.parameters[self.parameter]
		self.matrix = calclient.matrixFromPixelAndPositionShifts(self.image_pixelshifts[0], self.beam_positionshifts[0], self.image_pixelshifts[1], self.beam_positionshifts[1],self.camera['binning'])

	def saveCalibration(self):
		self.logger.info('Matrix saved')
		self.logger.debug('Matrix %s' % self.matrix)
		self.parameter = 'beam shift'
		calclient = self.parameters[self.parameter]
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		calclient.storeMatrix(self.scope['high tension'], self.scope['magnification'], self.parameter, self.matrix,tem,cam)
		self.beep()

	def prepareStep2(self):
		'''
		Prepare to move beam in x
		'''
		# update base image beam values to return to later
		self.getBaseImageBeamShift()
		self.moveImage('x')

	def prepareStep3(self):
		'''
		Prepare to move beam in y
		'''
		self.saveBeamShift('x')
		self.returnToBase()
		self.moveImage('y')

	def finish(self):
		'''
		Prepare to save calibration.
		'''
		self.saveBeamShift('y')
		self.returnToBase()
		self.calculateMatrix()

	def uiCalibrate(self):
		self.instrument_status = 'good'
		try:
			self.getBaseImageBeamShift()
			self.calibrate()
			# if all goes well, return here
			return
		except calibrationclient.NoPixelSizeError:
			self.logger.error(
								'Unable to get pixel size, aborting calibration')
		except CalibrationError, e:
			self.logger.error('Bad calibration measurement, aborting: %s', e)
		except Exception, e:
			self.logger.exception('Calibration failed: %s', e)
		except AttributeError, e:
			self.logger.exception('Calibration failed: %s', e)
		# abort in all error
		self.instrument_status = 'bad'
		self.uiAbort()

	def uiAbort(self):
		try:
			self.aborted.set()
			self.returnToBase()
		except AttributeError, e:
			# attribute error comes from base not assigned in uiCalibrate.
			# In other words, nothing has been done successfully.
			pass
		except Exception, e:
			raise
		self.logger.info('Calibration canceled')

	def getParameter(self):
		self.logger.info('%s current as base' % self.parameter)
		emdata = self.currentState()
		base = emdata[self.parameter].copy()
		return base

	def makeState(self, value, axis):
		return {axis: value}

	def getCurrentScopeCameraEMData(self):
		if self.instrument.tem is None:
			raise RuntimeError('cannot access TEM')
		emdata = self.currentState(leginondata.ScopeEMData)
		camdata = self.currentState(leginondata.CameraEMData)
		return emdata, camdata

