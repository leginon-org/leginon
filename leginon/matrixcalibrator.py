import calibrator
import event, data
import fftengine
import correlator
import peakfinder
import time
import camerafuncs
import calibrationclient

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
		calclient = self.parameters[self.parameter]

		## set cam state

		baselist = []
		for i in range(self.navg):
			delta = i * self.interval
			basex = self.base['x'] + delta
			basey = self.base['y'] + delta
			newbase = {'x':basex, 'y':basey}
			baselist.append(newbase)

		shifts = {}
		for axis in self.axislist:
			shifts[axis] = {'row': 0.0, 'col': 0.0}
			for base in baselist:
				print "axis =", axis
				basevalue = base[axis]

				print 'delta', self.delta
				newvalue = basevalue + self.delta
				print 'newvalue', newvalue

				state1 = self.makeState(basevalue, axis)
				state2 = self.makeState(newvalue, axis)
				print 'states', state1, state2
				shiftinfo = calclient.measureStateShift(state1, state2, 1, settle=self.settle[self.parameter])
				print 'shiftinfo', shiftinfo

				rowpix = shiftinfo['pixel shift']['row']
				colpix = shiftinfo['pixel shift']['col']
				totalpix = abs(rowpix + 1j * colpix)

				actual_states = shiftinfo['actual states']
				actual1 = actual_states[0][self.parameter][axis]
				actual2 = actual_states[1][self.parameter][axis]
				change = actual2 - actual1
				perpix = change / totalpix
				print '**PERPIX', perpix

				rowpixelsper = rowpix / change
				colpixelsper = colpix / change
				shifts[axis]['row'] += rowpixelsper
				shifts[axis]['col'] += colpixelsper
				print 'shifts', shifts

			shifts[axis]['row'] /= self.navg
			shifts[axis]['col'] /= self.navg

		mag = self.getMagnification()

		matrix = calclient.measurementToMatrix(shifts)
		calclient.storeMatrix(mag, self.parameter, matrix)

		print 'CALIBRATE DONE', shifts

	def defineUserInterface(self):
		nodespec = calibrator.Calibrator.defineUserInterface(self)

		camspec = self.cam.configUIData()

		#### parameters for user to set
		self.navg = 1
		self.delta = 2e-6
		self.interval = 2e-6


		try:
			curstate = self.currentState()
			self.base = curstate[self.parameter]
		except:
			self.base = {'x': 0.0, 'y':0.0}
		####

		cspec = self.registerUIMethod(self.uiCalibrate, 'Calibrate', ())

		parameters = self.registerUIData('paramdata', 'array', default=self.parameters.keys())

		argspec = (
		self.registerUIData('Parameter', 'string', choices=parameters, default='stage position'),
		self.registerUIData('N Average', 'float', default=self.navg),
		self.registerUIData('Base', 'struct', default=self.base),
		self.registerUIData('Delta', 'float', default=self.delta),
		self.registerUIData('Interval', 'float', default=self.interval),

		)

		rspec = self.registerUIMethod(self.uiSetParameters, 'Set Parameters', argspec)

		self.validshift = self.registerUIData('Valid Shift', 'struct', permissions='rw')
		self.validshift.set(
			{
			'correlation': {'min': 20.0, 'max': 512.0},
			'calibration': {'min': 20.0, 'max': 512.0}
			}
		)

		myspec = self.registerUISpec('Matrix Calibrator', (cspec, rspec, camspec))
		myspec += nodespec
		return nodespec

	def uiCalibrate(self):
		self.calibrate()
		return ''

	def uiSetParameters(self, parameter, navg, base, delta, interval):
		self.parameter = parameter
		self.navg = navg
		self.base = base
		self.delta = delta
		self.interval = interval
		return ''

	def makeState(self, value, axis):
		return {self.parameter: {axis: value}}

