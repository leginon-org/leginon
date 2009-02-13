#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import event, leginondata
from pyami import fftengine, correlator, peakfinder
import sys
import time
import calibrationclient
import threading
import node
import data
import gui.wx.MatrixCalibrator

class CalibrationError(Exception):
	pass

class Aborted(Exception):
	pass

class MatrixCalibrator(calibrator.Calibrator):
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
	panelclass = gui.wx.MatrixCalibrator.Panel
	settingsclass = leginondata.MatrixCalibratorSettingsData
	defaultsettings = calibrator.Calibrator.defaultsettings
	defaultsettings.update({
		'image shift tolerance': 12.0,
		'image shift shift fraction': 25.0,
		'image shift n average': 1,
		'image shift interval': 2e-6,
		'image shift current as base': True,
		'image shift base': {'x': 0.0, 'y': 0.0},
		'beam shift tolerance': 12.0,
		'beam shift shift fraction': 25.0,
		'beam shift n average': 1,
		'beam shift interval': 2e-6,
		'beam shift current as base': True,
		'beam shift base': {'x': 0.0, 'y': 0.0},
		'stage position tolerance': 12.0,
		'stage position shift fraction': 25.0,
		'stage position n average': 1,
		'stage position interval': 2e-6,
		'stage position current as base': True,
		'stage position base': {'x': 0.0, 'y': 0.0},
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)

		self.parameters = {
		  'image shift': calibrationclient.ImageShiftCalibrationClient(self),
		  'beam shift': calibrationclient.BeamShiftCalibrationClient(self),
		  'stage position': calibrationclient.StageCalibrationClient(self)
		}
		self.parameter = 'stage position'
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.settle = {
		  'image shift': 5.0,
		  'beam shift': 1.0,
		  'stage position': 1.0
		}

		self.axislist = ['x', 'y']
		self.aborted = threading.Event()

		self.start()

	# calibrate needs to take a specific value
	def calibrate(self):
		if self.initInstruments():
			return
		self.aborted.clear()

		calclient = self.parameters[self.parameter]

		basebase = self.getBase()
		baselist = []
		naverage = self.settings['%s n average' % self.parameter]
		for i in range(naverage):
			delta = i * self.settings['%s interval' % self.parameter]
			basex = basebase['x'] + delta
			basey = basebase['y'] + delta
			newbase = {'x':basex, 'y':basey}
			baselist.append(newbase)

		## calculate delta based on pixel size and camera config
		## use 1/4 image width to calculate delta
		## delta = dimension['x'] * binning['x'] * pixsize / 4
		mag, mags = self.getMagnification()
		pixsize = self.pixsizeclient.retrievePixelSize(None, None, mag)

		percent = self.settings['%s shift fraction' % self.parameter]/100.0
		delta = percent * self.instrument.ccdcamera.Dimension['x']*self.instrument.ccdcamera.Binning['x']*pixsize
		self.logger.debug('Delta %s' % delta)

		shifts = {}
		for axis in self.axislist:
			shifts[axis] = {'row': 0.0, 'col': 0.0}
			n = 0
			for base in baselist:
				self.logger.info('Calibrating %s axis...' % axis)
				basevalue = base[axis]

				### 
				newvalue = basevalue + delta
				self.logger.debug('New value %s' % newvalue)

				state1 = self.makeState(basevalue, axis)
				state2 = self.makeState(newvalue, axis)
				self.logger.debug('States %s, %s' % (state1, state2))
				im1 = calclient.acquireImage(state1, settle=self.settle[self.parameter])
				shiftinfo = calclient.measureScopeChange(im1, state2, settle=self.settle[self.parameter])

				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				self.logger.info('Shift between images: (%.2f, %.2f)' % (colpix, rowpix))
				totalpix = abs(rowpix + 1j * colpix)
				if totalpix == 0.0:
					raise CalibrationError('total pixel shift is zero')

				actual1 = shiftinfo['previous']['scope'][self.parameter][axis]
				actual2 = shiftinfo['next']['scope'][self.parameter][axis]
				change = actual2 - actual1
				if change == 0.0:
					raise CalibrationError('change in %s is zero' % self.parameter)

				perpix = change / totalpix

				## deviation from pixsize should be less than
				## 12%
				#tol = 12/100.0
				tol = self.settings['%s tolerance' % self.parameter]/100.0
				err = abs(perpix - pixsize) / pixsize

				s = 'Pixel size error: %.2f' % (err*100.0)
				s += '%'
				s += ' (per pixel %s)' % perpix
				self.logger.info(s)

				if err > tol:
					self.logger.warning('Failed pixel size tolerance')
					continue

				rowpixelsper = rowpix / change
				colpixelsper = colpix / change
				shifts[axis]['row'] += rowpixelsper
				shifts[axis]['col'] += colpixelsper
				n += 1

				if self.aborted.isSet():
					raise Aborted()

			if n:
				shifts[axis]['row'] /= n
				shifts[axis]['col'] /= n
			else:
				# this axis was a failure
				# better just fail the whole calibration
				raise CalibrationError('no successful calibration measurement')

		# return to base
		emdata = leginondata.ScopeEMData()
		emdata[self.parameter] = basebase
		self.instrument.setData(emdata)

		mag, mags = self.getMagnification()
		ht = self.getHighTension()

		matrix = calclient.measurementToMatrix(shifts)
		self.logger.debug('Matrix %s' % matrix)
		calclient.storeMatrix(ht, mag, self.parameter, matrix)
		self.beep()

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
		self.aborted.set()

	def getBase(self):
		if self.settings['%s current as base' % self.parameter]:
			emdata = self.currentState()
			base = emdata[self.parameter]
		else:
			base = self.settings['%s base' % self.parameter]
		return base

	def makeState(self, value, axis):
		return {self.parameter: {axis: value}}

	def getCurrentCalibration(self):
		if self.instrument.tem is None:
			raise RuntimeError('cannot access TEM')
		try:
			calclient = self.parameters[self.parameter]
		except KeyError:
			raise RuntimeError('no parameter selected')
		tem = self.instrument.getTEMData()
		cam = self.instrument.getCCDCameraData()
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
		p2 = stagecal.pixelToPixel(tem, cam, ht, mag1, mag2, p1)
		return p2
