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
import Numeric
import Mrc
import uidata
import threading
import node

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
	def __init__(self, id, session, managerlocation, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, managerlocation, **kwargs)

		self.parameters = {
		  'image shift': calibrationclient.ImageShiftCalibrationClient(self),
		  'beam shift': calibrationclient.BeamShiftCalibrationClient(self),
		  'stage position': calibrationclient.StageCalibrationClient(self)
		}
		self.pixsizeclient = calibrationclient.PixelSizeCalibrationClient(self)
		self.settle = {
		  'image shift': 0.25,
		  'beam shift': 0.25,
		  'stage position': 5.0
		}

		self.axislist = ['x', 'y']
		self.aborted = threading.Event()

		self.defineUserInterface()
		self.start()

	# calibrate needs to take a specific value
	def calibrate(self):
		uiparameter = self.uiparameter.getSelectedValue()
		calclient = self.parameters[uiparameter]

		## set cam state
		self.cam.uiApplyAsNeeded()

		basebase = self.getBase()
		baselist = []
		for i in range(self.uinaverage.get()):
			delta = i * self.ui_interval.get()
			basex = basebase['x'] + delta
			basey = basebase['y'] + delta
			newbase = {'x':basex, 'y':basey}
			baselist.append(newbase)

		## calculate delta based on pixel size and camera config
		## use 1/4 image width to calculate delta
		## delta = dimension['x'] * binning['x'] * pixsize / 4
		mag = self.getMagnification()
		pixsize = self.pixsizeclient.retrievePixelSize(mag)
		camconfig = self.cam.getCameraEMData()

		percent = self.shiftpercent.get()
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
				shiftinfo = calclient.measureStateShift(state1, state2, 1, settle=self.settle[uiparameter])

				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				self.logger.info('shift %s rows, %s cols' % (rowpix, colpix))
				totalpix = abs(rowpix + 1j * colpix)

				actual_states = shiftinfo['actual states']
				actual1 = actual_states[0][uiparameter][axis]
				actual2 = actual_states[1][uiparameter][axis]
				change = actual2 - actual1
				perpix = change / totalpix
				self.logger.info('Per pixel %s' % perpix)

				## deviation from pixsize should be less than
				## 12%
				#tol = 0.12
				tol = self.uitolerance.get()
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
				self.logger.info('Shifts %s' % shifts)

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
		emdata[uiparameter] = basebase
		self.emclient.setScope(emdata)

		mag = self.getMagnification()
		ht = self.getHighTension()

		matrix = calclient.measurementToMatrix(shifts)
		self.logger.info('Matrix %s' % matrix)
		calclient.storeMatrix(ht, mag, uiparameter, matrix)
		node.beep()

	def fakeCalibration(self):
		ht = self.getHighTension()
		mag = self.getMagnification()
		uiparameter = self.uiparameter.getSelectedValue()
		matrix = Numeric.zeros((2,2))
		calclient = self.parameters[uiparameter]
		calclient.storeMatrix(ht, mag, uiparameter, matrix)

	def defineUserInterface(self):
		calibrator.Calibrator.defineUserInterface(self)

		self.uitolerance = uidata.Float('Tolerance', 0.12, 'rw', persist=True)
		self.shiftpercent = uidata.Float('Shift Fraction', 0.25, 'rw', persist=True)
		parameters = self.parameters.keys()
		parameters.sort()
		self.uiparameter = uidata.SingleSelectFromList('Parameter', parameters, 0, persist=True)
		self.uinaverage = uidata.Integer('N Average', 1, 'rw')
		self.ui_interval = uidata.Float('Interval', 2e-6, 'rw')
		self.uicurbase = uidata.Boolean('Current as Base', True, 'rw')
		self.uibase = uidata.Struct('Base', {'x':0,'y':0}, 'rw')
		#self.uidelta = uidata.Float('Delta', 2e-6, 'rw')
		validshift = {'correlation': {'min': 20.0, 'max': 512.0},
  							   'calibration': {'min': 20.0, 'max': 512.0}}
		#self.uivalidshift = uidata.Struct('Valid Shift', validshift, 'rw')

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.uitolerance, self.shiftpercent, self.uiparameter, self.uinaverage, self.ui_interval, self.uicurbase, self.uibase))

		calibratemethod = uidata.Method('Calibrate', self.uiCalibrate)
		abortmethod = uidata.Method('Abort', self.uiAbort)
		fakecalibrationmethod = uidata.Method('Fake Calibration',
																				self.fakeCalibration)

		container = uidata.LargeContainer('Matrix Calibrator')
		container.addObjects((settingscontainer, calibratemethod, abortmethod,
													fakecalibrationmethod))
		self.uicontainer.addObject(container)

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
		param = self.uiparameter.getSelectedValue()
		self.saveparam = self.emclient.getScope()[param]
		self.logger.info('Storing parameter %s, %s'
											% (param, self.saveparam))

	def setParameter(self):
		self.logger.info('Returning to original state')
		param = self.uiparameter.getSelectedValue()
		emdata = data.ScopeEMData()
		emdata[param] = self.saveparam
		self.emclient.setScope(emdata)

	def uiAbort(self):
		self.aborted.set()

	def getBase(self):
		if self.uicurbase.get():
			param = self.uiparameter.getSelectedValue()
			emdata = self.currentState()
			base = emdata[param]
		else:
			base = self.uibase.get()
		return base

	def makeState(self, value, axis):
		return {self.uiparameter.getSelectedValue(): {axis: value}}

