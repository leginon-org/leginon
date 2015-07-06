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
	Calibrates a microscope parameter with image pixel coordinates.
	Configure in the 'Set Parameters' section:
	  'Parameter':  microscope parameter
	  'N Average':  how many measurements to average, each 
	     measurement is seperated by 'Interval'
	  'Base':  where to start (this is a little weird now)
	  'Delta':  amount to shift the parameter in measurement
	  'Camera State':  camera configuration
	  Then 'Set Parameters'
	Then 'Calibrate'
	(Valid Shift is currently being ignored)
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
		self.userpause = threading.Event()

		self.start()

	# calibrate needs to take a specific value
	def calibrate(self):
		if self.initInstruments():
			return
		self.aborted.clear()

		calclient = self.parameters[self.parameter]

		# This gives base for beam shift
		self.parameter = 'beam shift'
		beambase = self.getBase()
		self.parameter = 'image shift'
		imagebase = self.getBase()

		mag, mags = self.getMagnification()
		pixsize = self.pixsizeclient.retrievePixelSize(None, None, mag)

		cam = self.instrument.ccdcamera
		delta = self.settings['image shift delta']
		self.logger.debug('Delta %s' % delta)

		image_pixelshift_matrix = numpy.matrix(((0.0,0.0),(0.0,0.0)))
		beam_positionshift_matrix = numpy.matrix(((0.0,0.0),(0.0,0.0)))

		for i,axis in enumerate(self.axislist):
			# get pixel shift by image shift
			self.parameter = 'image shift'
			position = {'x':0.0,'y':0.0}
			position[axis] = delta
			calclient = self.parameters[self.parameter]
			scope, camera = self.getCurrentTEMCameraData()
			# shift in pixel for the camera config
			shift = calclient.itransform(position, scope, camera)
			# TO DO: shifts -> shiftinfo ?
			rowpix = shift['row']
			colpix = shift['col']
			totalpix = abs(rowpix + 1j * colpix)
			image_pixelshift_matrix[i] = (rowpix,colpix)

			### set image shift
			basevalue = imagebase[axis]
			newvalue = basevalue + delta
			self.logger.debug('New value %s' % newvalue)

			state1 = self.makeState(basevalue, axis)
			state2 = self.makeState(newvalue, axis)
			self.instrument.tem.ImageShift = state2
			self.logger.debug('States %s, %s' % (state1, state2))

			self.logger.info('Shift between images: (%.2f, %.2f)' % (colpix, rowpix))
			if totalpix == 0.0:
				raise CalibrationError('total pixel shift is zero')

			# ui move beam
			self.parameter = 'beam shift'
			newbeamstate = self.uiMoveBeam(axis)
			self.logger.info('got new state')
			if self.aborted.isSet():
				raise Aborted()


			if newbeamstate == beambase:
				raise CalibrationError('change in %s is zero' % self.parameter)
			beamchange = {'x':newbeamstate['x']-beambase['x'],'y':newbeamstate['y']-beambase['y']}
			self.logger.info('scope %s axis % s change : (x,y)=(%s,%s)' % (self.parameter,axis,beamchange['x'],beamchange['y']))

			beam_positionshift_matrix[i] = (beamchange['x'],beamchange['y'])

			if self.aborted.isSet():
				raise Aborted()

		# return to base
		emdata = leginondata.ScopeEMData()
		emdata['image shift'] = imagebase
		emdata['beam shift'] = beambase
		self.instrument.setData(emdata)

		mag, mags = self.getMagnification()
		ht = self.getHighTension()

		matrix = calclient.matrixFromPixelAndPositionShift((-1)*image_pixelshift_matrix, beam_positionshift_matrix, camera['binning']['x'])
		print matrix
		self.logger.info('Matrix saved')
		self.logger.debug('Matrix %s' % matrix)
		calclient.storeMatrix(ht, mag, self.parameter, matrix)
		self.beep()

	def uiMoveBeam(self, axis='x'):
		self.setStatus('user input')
		self.logger.info('wait for user to move beam back to center')
		value = {'x':0.0,'y':0.0}
		value[axis] = value[axis]+2e-6
		self.instrument.tem.BeamShift = value
		base = self.panel.moveBeam(axis)
		return base

	def uiMoveBeamDone(self):
		self.userpause.clear()
		return self.getBase()
		
	def uiCalibrate(self):
		try:
			self.getParameter()
		except Exception, e:
			self.logger.exception('Unable to get parameter, aborting calibration: %s', e)
			self.panel.calibrationDone()
			return

		try:
			self.calibrate()
		except calibrationclient.NoPixelSizeError:
			self.logger.error(
								'Unable to get pixel size, aborting calibration')
		except CalibrationError, e:
			self.logger.error('Bad calibration measurement, aborting: %s', e)
		except Exception, e:
			raise
			self.logger.exception('Calibration failed: %s', e)
		else:
			self.logger.info('Calibration completed successfully')
		# return to original state
		try:
			self.setParameter()
		except Exception, e:
			self.logger.exception('Could not return to original state: %s', e)
		self.panel.calibrationDone()

	def getParameter(self):
		self.saveparam = self.instrument.getData(leginondata.ScopeEMData)[self.parameter]
		self.logger.debug('Storing parameter %s, %s'
											% (self.parameter, self.saveparam))

	def setParameter(self):
		self.logger.info('Returning to original state')
		emdata = leginondata.ScopeEMData()
		emdata[self.parameter] = self.saveparam
		self.instrument.setData(emdata)

	def uiAbort(self):
		self.userpause.clear()
		self.aborted.set()

	def getBase(self):
		self.logger.info('%s current as base' % self.parameter)
		emdata = self.currentState()
		base = emdata[self.parameter]
		return base

	def makeState(self, value, axis):
		return {self.parameter: {axis: value}}

	def getCurrentTEMCameraData(self):
		if self.instrument.tem is None:
			raise RuntimeError('cannot access TEM')
		emdata = self.currentState(leginondata.ScopeEMData)
		camdata = self.currentState(leginondata.CameraEMData)
		return emdata, camdata

	def getCurrentCalibration(self):
		try:
			calclient = self.parameters[self.parameter]
		except KeyError:
			raise RuntimeError('no parameter selected')
		tem, cam = self.getCurrentTEMCameraData()
		par = self.parameter
		ht = self.instrument.tem.HighTension
		mag = self.instrument.tem.Magnification
		return calclient.researchMatrix(tem, cam, par, ht, mag)

	def editCurrentCalibration(self):
		try:
			calibrationdata = self.getCurrentCalibration()
		except calibrationclient.NoMatrixCalibrationError, e:
			if e.state is None:
				raise e
			else:
				self.logger.warning('No calibration found for current state: %s' % e)
				calibrationdata = e.state
		except Exception, e:
			self.logger.error('Calibration edit failed: %s' % e)
			return
		self.panel.editCalibration(calibrationdata)

	def saveCalibration(self, matrix, parameter, ht, mag, tem, ccdcamera):
		try:
			calclient = self.parameters[parameter]
		except KeyError:
			raise RuntimeError('no parameter selected')
		calclient.storeMatrix(ht, mag, parameter, matrix, tem, ccdcamera)

	def pixelToPixel(self, mag1, mag2, p1):
		stagecal = self.parameters['stage position']
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
		ht = self.instrument.tem.HighTension
		p2 = stagecal.pixelToPixel(tem, cam, tem, cam, ht, mag1, mag2, p1)
		return p2
