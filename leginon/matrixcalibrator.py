import calibrator
import event, data
import fftengine
import correlator
import peakfinder
import time
import camerafuncs
import calibrationclient
import Numeric

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
		calclient = self.parameters[self.parameter.get()]

		## set cam state

		baselist = []
		for i in range(self.navg.get()):
			delta = i * self.interval.get()
			basex = self.base.get()['x'] + delta
			basey = self.base.get()['y'] + delta
			newbase = {'x':basex, 'y':basey}
			baselist.append(newbase)

		shifts = {}
		for axis in self.axislist:
			shifts[axis] = {'row': 0.0, 'col': 0.0}
			for base in baselist:
				print "axis =", axis
				basevalue = base[axis]

				print 'delta', self.delta.get()
				newvalue = basevalue + self.delta.get()
				print 'newvalue', newvalue

				state1 = self.makeState(basevalue, axis)
				state2 = self.makeState(newvalue, axis)
				print 'states', state1, state2
				shiftinfo = calclient.measureStateShift(state1, state2, 1, settle=self.settle[self.parameter.get()])
				self.image1.set(calclient.numimage1)
				self.image2.set(calclient.numimage2)
				print 'shiftinfo', shiftinfo

				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				totalpix = abs(rowpix + 1j * colpix)

				actual_states = shiftinfo['actual states']
				actual1 = actual_states[0][self.parameter.get()][axis]
				actual2 = actual_states[1][self.parameter.get()][axis]
				change = actual2 - actual1
				perpix = change / totalpix
				print '**PERPIX', perpix

				rowpixelsper = rowpix / change
				colpixelsper = colpix / change
				shifts[axis]['row'] += rowpixelsper
				shifts[axis]['col'] += colpixelsper
				print 'shifts', shifts

			shifts[axis]['row'] /= self.navg.get()
			shifts[axis]['col'] /= self.navg.get()

		mag = self.getMagnification()

		matrix = calclient.measurementToMatrix(shifts)
		print 'MATRIX', matrix
		print 'MATRIX shape', matrix.shape
		print 'MATRIX type', matrix.typecode()
		print 'MATRIX flat', Numeric.ravel(matrix)
		calclient.storeMatrix(mag, self.parameter.get(), matrix)

		print 'CALIBRATE DONE', shifts

	def defineUserInterface(self):
		nodespec = calibrator.Calibrator.defineUserInterface(self)

		camspec = self.cam.configUIData()


		cspec = self.registerUIMethod(self.uiCalibrate, 'Calibrate', ())

		parameters = self.registerUIData('paramdata', 'array',	
																			default=self.parameters.keys())
		self.navg = self.registerUIData('N Average', 'float', permissions='rw',
																																	default=1)

		self.base = self.registerUIData('Base', 'struct', permissions='rw')
		self.parameter = self.registerUIData('Parameter', 'string',
																					choices=parameters, permissions='rw',
																					default='stage position',
																					callback=self.uiParameterCallback)
		self.delta = self.registerUIData('Delta', 'float', permissions='rw',
																														default=2e-6)
		self.interval = self.registerUIData('Interval', 'float', permissions='rw',
																																	default=2e-6)

		argspec = (self.parameter, self.navg, self.base, self.delta, self.interval)
		rspec = self.registerUIContainer('Parameters', argspec)

		self.image1 = self.registerUIData('Image 1', 'binary', permissions='r')
		self.image2 = self.registerUIData('Image 2', 'binary', permissions='r')
		imagespec = self.registerUIContainer('Images', (self.image1, self.image2))

		self.validshift = self.registerUIData('Valid Shift', 'struct',
																									permissions='rw')
		self.validshift.set(
			{
			'correlation': {'min': 20.0, 'max': 512.0},
			'calibration': {'min': 20.0, 'max': 512.0}
			}
		)

		myspec = self.registerUISpec('Matrix Calibrator', (cspec, rspec, camspec, imagespec))
		myspec += nodespec
		return nodespec

	def uiCalibrate(self):
		self.calibrate()
		return ''

	def uiParameterCallback(self, value=None):
		if value is not None:
			self.parametervalue = value
			try:
				curstate = self.currentState()
				self.base.set(curstate[self.parametervalue])
			except:
				self.base.set({'x': 0.0, 'y':0.0})
		return self.parametervalue

	def makeState(self, value, axis):
		return {self.parameter: {axis: value}}

