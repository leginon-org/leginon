#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import calibrator
import event, data
import fftengine
import correlator
import peakfinder
import sys
import time
import camerafuncs
import calibrationclient
try:
	import numarray as Numeric
except:
	import Numeric
import uidata
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
	settingsclass = data.MatrixCalibratorSettingsData
	defaultsettings = {
		'camera settings': None,
		'correlation type': 'cross',
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
	}
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
		  'image shift': 0.25,
		  'beam shift': 0.25,
		  'stage position': 5.0
		}

		self.axislist = ['x', 'y']
		self.aborted = threading.Event()

		self.start()

	# calibrate needs to take a specific value
	def calibrate(self):
		calclient = self.parameters[self.parameter]

		## set cam state
		self.cam.setCameraDict(self.settings['camera settings'])

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
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		camconfig = self.cam.getCameraEMData()

		percent = self.settings['%s shift fraction' % self.parameter]/100.0
		delta = percent * camconfig['dimension']['x']*camconfig['binning']['x']*pixsize
		self.logger.info('Delta %s' % delta)

		self.aborted.clear()

		shifts = {}
		for axis in self.axislist:
			shifts[axis] = {'row': 0.0, 'col': 0.0}
			n = 0
			for base in baselist:
				self.logger.info('Axis %s' % axis)
				basevalue = base[axis]

				### 
				newvalue = basevalue + delta
				self.logger.info('New value %s' % newvalue)

				state1 = self.makeState(basevalue, axis)
				state2 = self.makeState(newvalue, axis)
				self.logger.info('States %s, %s' % (state1, state2))
				shiftinfo = calclient.measureStateShift(state1, state2, 1, settle=self.settle[self.parameter])

				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				self.logger.info('shift %s rows, %s cols' % (rowpix, colpix))
				totalpix = abs(rowpix + 1j * colpix)

				actual_states = shiftinfo['actual states']
				actual1 = actual_states[0][self.parameter][axis]
				actual2 = actual_states[1][self.parameter][axis]
				change = actual2 - actual1
				perpix = change / totalpix
				self.logger.info('Per pixel %s' % perpix)

				## deviation from pixsize should be less than
				## 12%
				#tol = 12/100.0
				tol = self.settings['%s tolerance' % self.parameter]/100.0
				err = abs(perpix - pixsize) / pixsize
				if err > tol:
					self.logger.warning('Failed pixel size tolerance')
					continue

				if change == 0.0:
					raise CalibrationError()
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
				raise CalibrationError()

		# return to base
		emdata = data.ScopeEMData()
		emdata[self.parameter] = basebase
		self.emclient.setScope(emdata)

		mag, mags = self.getMagnification()
		ht = self.getHighTension()

		matrix = calclient.measurementToMatrix(shifts)
		self.logger.info('Matrix %s' % matrix)
		calclient.storeMatrix(ht, mag, self.parameter, matrix)
		self.beep()

	def fakeCalibration(self):
		ht = self.getHighTension()
		mag, mags = self.getMagnification()
		matrix = Numeric.zeros((2,2))
		calclient = self.parameters[self.parameter]
		calclient.storeMatrix(ht, mag, self.parameter, matrix)

	def uiCalibrate(self):
		self.getParameter()
		try:
			self.calibrate()
		except calibrationclient.NoPixelSizeError:
			self.logger.error(
								'Cannot get pixel size for current state, halting calibration')
		except CalibrationError:
			self.logger.error('No good measurement, halting calibration')
		except camerafuncs.NoCorrectorError:
			self.logger.error(
										'Cannot get corrected images, Corrector may not be running')
		except:
			self.logger.exception('exception in self.calibrate()')
		else:
			self.logger.info('Calibration completed successfully')
		# return to original state
		self.setParameter()

	def getParameter(self):
		self.saveparam = self.emclient.getScope()[self.parameter]
		self.logger.info('Storing parameter %s, %s'
											% (param, self.saveparam))

	def setParameter(self):
		self.logger.info('Returning to original state')
		emdata = data.ScopeEMData()
		emdata[self.parameter] = self.saveparam
		self.emclient.setScope(emdata)

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

