import calibrator
import event, data
import fftengine
import correlator
import peakfinder
import time
import camerafuncs
import calibrationclient
import Numeric
import Mrc
import uidata

False=0
True=1

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
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)

		self.parameters = {
		  'image shift': calibrationclient.ImageShiftCalibrationClient(self),
		  'beam shift': calibrationclient.BeamShiftCalibrationClient(self),
		  'stage position': calibrationclient.StageCalibrationClient(self)
		}
		self.settle = {
		  'image shift': 0.25,
		  'beam shift': 0.25,
		  'stage position': 1.5
		}

		self.axislist = ['x', 'y']

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 500
		self.cam.config(currentconfig)

		self.defineUserInterface()
		self.start()

	# calibrate needs to take a specific value
	def calibrate(self):
		uiparameter = self.uiparameter.getSelectedValue()[0]
		calclient = self.parameters[uiparameter]

		## set cam state

		baselist = []
		for i in range(self.uinaverage.get()):
			delta = i * self.ui_interval.get()
			basex = self.uibase.get()['x'] + delta
			basey = self.uibase.get()['y'] + delta
			newbase = {'x':basex, 'y':basey}
			baselist.append(newbase)

		shifts = {}
		for axis in self.axislist:
			shifts[axis] = {'row': 0.0, 'col': 0.0}
			for base in baselist:
				print "axis =", axis
				basevalue = base[axis]

				print 'delta', self.uidelta.get()
				newvalue = basevalue + self.uidelta.get()
				print 'newvalue', newvalue

				state1 = self.makeState(basevalue, axis)
				state2 = self.makeState(newvalue, axis)
				print 'states', state1, state2
				shiftinfo = calclient.measureStateShift(state1, state2, 1, settle=self.settle[uiparameter])
				self.image1.set(calclient.numimage1)
				self.image2.set(calclient.numimage2)
				print 'shiftinfo', shiftinfo

				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				totalpix = abs(rowpix + 1j * colpix)

				actual_states = shiftinfo['actual states']
				actual1 = actual_states[0][uiparameter][axis]
				actual2 = actual_states[1][uiparameter][axis]
				change = actual2 - actual1
				perpix = change / totalpix
				print '**PERPIX', perpix

				rowpixelsper = rowpix / change
				colpixelsper = colpix / change
				shifts[axis]['row'] += rowpixelsper
				shifts[axis]['col'] += colpixelsper
				print 'shifts', shifts

			shifts[axis]['row'] /= self.uinaverage.get()
			shifts[axis]['col'] /= self.uinaverage.get()

		mag = self.getMagnification()

		matrix = calclient.measurementToMatrix(shifts)
		print 'MATRIX', matrix
		print 'MATRIX shape', matrix.shape
		print 'MATRIX type', matrix.typecode()
		print 'MATRIX flat', Numeric.ravel(matrix)
		calclient.storeMatrix(mag, uiparameter, matrix)

		print 'CALIBRATE DONE', shifts

	def defineUserInterface(self):
		calibrator.Calibrator.defineUserInterface(self)
		cameraconfig = self.cam.configUIData()
		self.uinaverage = uidata.UIInteger('N Average', 1, 'rw')
		self.uibase = uidata.UIStruct('Base', {}, 'rw')
		parameters = self.parameters.keys()
		if parameters:
			parameters.sort()
			selected = [0]
		else:
			selected = []
		self.uiparameter = uidata.UISelectFromList('Parameter', parameters,
																								selected, 'r',
																								self.uiParameterCallback)
		self.uidelta = uidata.UIFloat('Delta', 2e-6, 'rw')
		self.ui_interval = uidata.UIFloat('Interval', 2e-6, 'rw')
		validshift = {'correlation': {'min': 20.0, 'max': 512.0},
  							   'calibration': {'min': 20.0, 'max': 512.0}}
		self.uivalidshift = uidata.UIStruct('Valid Shift', validshift, 'rw')

		settingscontainer = uidata.UIContainer('Settings')
		settingscontainer.addUIObjects((cameraconfig, self.uinaverage, self.uibase,
																		self.uiparameter, self.uidelta,
																		self.ui_interval, self.uivalidshift))

		calibratemethod = uidata.UIMethod('Calibrate', self.uiCalibrate)

		self.image1 = uidata.UIImage('Image 1', None, 'r')
		self.image2 = uidata.UIImage('Image 2', None, 'r')
		imagecontainer = uidata.UIContainer('Images')
		imagecontainer.addUIObjects((self.image1, self.image2))

		container = uidata.UIMediumContainer('Matrix Calibrator')
		container.addUIObjects((settingscontainer, calibratemethod, imagecontainer))
		self.uiserver.addUIObject(container)

	def uiCalibrate(self):
		self.calibrate()
		return ''

	def uiParameterCallback(self, value):
		try:
			curstate = self.currentState()
			self.uibase.set(curstate[value])
		except:
			self.uibase.set({'x': 0.0, 'y':0.0})
		return value

	def makeState(self, value, axis):
		return {self.uiparameter.getSelectedValue()[0]: {axis: value}}

