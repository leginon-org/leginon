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

		self.image_pixelshift_matrix = numpy.array(numpy.matrix(((0.0,0.0),(0.0,0.0))))
		self.beam_positionshift_matrix = numpy.array(numpy.matrix(((0.0,0.0),(0.0,0.0))))
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
		# TO DO: shifts -> shiftinfo ?
		rowpix = shift['row']
		colpix = shift['col']
		self.image_pixelshift_matrix[i] = (rowpix,colpix)

		### set image shift
		basevalue = self.imagebase[axis]
		newvalue = basevalue + delta
		self.logger.debug('New value %s' % newvalue)

		state1 = self.makeState(basevalue, axis)
		state2 = self.makeState(newvalue, axis)
		self.instrument.tem.ImageShift = state2
		self.logger.debug('States %s, %s' % (state1, state2))

		self.logger.info('Shift between images: (%.2f, %.2f)' % (colpix, rowpix))

	def saveBeamShift(self,axis):	
		i = self.axismap[axis]
		# ui move beam
		self.parameter = 'beam shift'
		newbeamstate = self.instrument.tem.BeamShift
		# simulator test
		newbeamstate[axis] = newbeamstate[axis]+1e-6
		self.logger.info('got new state')

		if newbeamstate == self.beambase:
			raise CalibrationError('change in %s is zero' % self.parameter)
		beamchange = {'x':newbeamstate['x']-self.beambase['x'],'y':newbeamstate['y']-self.beambase['y']}
		self.logger.info('scope %s axis % s change : (x,y)=(%s,%s)' % (self.parameter,axis,beamchange['x'],beamchange['y']))

		self.beam_positionshift_matrix[i] = (beamchange['x'],beamchange['y'])

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
		self.matrix = calclient.matrixFromPixelAndPositionShift((-1)*self.image_pixelshift_matrix, self.beam_positionshift_matrix, self.camera['binning']['x'])

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
		base = emdata[self.parameter]
		return base

	def makeState(self, value, axis):
		return {self.parameter: {axis: value}}

	def getCurrentScopeCameraEMData(self):
		if self.instrument.tem is None:
			raise RuntimeError('cannot access TEM')
		emdata = self.currentState(leginondata.ScopeEMData)
		camdata = self.currentState(leginondata.CameraEMData)
		return emdata, camdata

