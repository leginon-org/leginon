import node
import data
import fftengine
import correlator
import peakfinder
import sys
import event
import time
import Numeric
import LinearAlgebra
import cPickle
import cameraimage
import camerafuncs
reload(camerafuncs)

False=0
True=1

class Calibration(node.Node, camerafuncs.CameraFuncs):
	def __init__(self, id, nodelocations):

		ffteng = fftengine.fftNumeric()
		#ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()

		self.axislist = ['x', 'y']
		self.settle = 2.0

		self.calibration = {}
		self.clearStateImages()

		node.Node.__init__(self, id, nodelocations)
		
	def calculatePixelFromPercent(self, percent):
		pixel = {'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}}
		for axis in percent:
			for limit in percent[axis]:
				pixel[axis][limit] = self.camerastate['size'] \
						* percent[axis][limit]/100
		return pixel

	def calculatePercentFromPixel(self, pixel):
		percent = {'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}}
		for axis in pixel:
			for limit in pixel[axis]:
				percent[axis][limit] = \
					pixel[axis][limit] / self.camerastate['size'] * 100
		return percent

	def main(self):
		pass

	def state(self, value, axis):
		raise NotImplementedError()

	# calibrate needs to take a specific value
	def calibrate(self):
		self.clearStateImages()
		adjustedrange = self.range

		size = self.camerastate['size']
		bin = self.camerastate['binning']
		exp = self.camerastate['exposure time']
		camstate = {
			"dimension": {'x': size, 'y': size},
			"binning": {'x': bin, 'y': bin},
			"exposure time": exp
		}
		self.cameraDefaultOffset(camstate)

		camdata = data.EMData('camera', camstate)

		self.publish(event.LockEvent(self.ID()))
		self.publishRemote(camdata)

		# might reuse value from previous axis
		for axis in self.axislist:
			print "axis =", axis
			basevalue = self.base[axis]
			for i in range(self.attempts):
				print "attempt =", i
				delta = (adjustedrange[1] - adjustedrange[0]) / 2 + adjustedrange[0]
				print 'delta', delta
				newvalue = basevalue + delta
				print 'newvalue', newvalue

				state1 = self.state(basevalue, axis)
				state2 = self.state(newvalue, axis)
				print 'states', state1, state2
				shiftinfo = self.measureStateShift(state1, state2)
				print 'shiftinfo', shiftinfo

				verdict = self.validateShift(shiftinfo)

				if verdict == 'good':
					print "good"
					self.calibration.update({axis + " pixel shift": {'x':shiftinfo['shift'][1], 'y':shiftinfo['shift'][0], 'value': delta}})
					break
				elif verdict == 'small':
					print "too small"
					adjustedrange[0] = delta
				elif verdict == 'big':
					print "too big"
					adjustedrange[1] = delta

			basestate = self.state(self.base[axis], axis)
			self.publishRemote(data.EMData('scope', basestate))

		self.publish(event.UnlockEvent(self.ID()))

		print 'CALIBRATE DONE', self.calibration

	def clearStateImages(self):
		self.images = []

	def acquireStateImage(self, state):
		## determine if this state is already acquired
		for info in self.images:
			if info['state'] == state:
				image = info['image']
				return info

		## acquire image at this state
		newemdata = data.EMData('scope', state)
		self.publish(event.LockEvent(self.ID()))
		self.publishRemote(newemdata)
		print 'state settling time %s' % (self.settle,)
		time.sleep(self.settle)
		print 'getting image data'

		emdata = self.researchByDataID('image data')
		self.publish(event.UnlockEvent(self.ID()))
		image = emdata.content['image data']

		imagedata = data.ImageData(self.ID(), image)
		self.publish(imagedata, event.ImagePublishEvent)
		## should find image stats to help determine validity of image
		## in correlations
		image_stats = None

		info = {'state': state, 'image': image, 'image stats': image_stats}
		self.images.append(info)
		return info

	def measureStateShift(self, state1, state2):
		'''measures the pixel shift between two states'''

		print 'acquiring state images'
		info1 = self.acquireStateImage(state1)
		info2 = self.acquireStateImage(state2)

		image1 = info1['image']
		image2 = info2['image']
		stats1 = info1['image stats']
		stats2 = info2['image stats']

		shiftinfo = {}

		self.correlator.insertImage(image1)

		## could autocorrelation here help also?
		autocorr = 0
		if autocorr:
			self.correlator.insertImage(image1)
			acimage = self.correlator.phaseCorrelate()
			self.peakfinder.setImage(acimage)
			self.peakfinder.subpixelPeak()
			peak = self.peakfinder.getResults()
			acpeakvalue = peak['subpixel peak value']
			acshift = correlator.wrap_coord(peak['subpixel peak'], acimage.shape)
			shiftinfo.update({'ac shift':acshift,'ac peak value':acpeakvalue})
			acimagedata = data.ImageData(self.ID(), acimage)
			self.publish(acimagedata, event.PhaseCorrelationImagePublishEvent)

		## phase correlation
		self.correlator.insertImage(image2)
		print 'correlation'
		pcimage = self.correlator.phaseCorrelate()

		pcimagedata = data.ImageData(self.ID(), pcimage)
		self.publish(pcimagedata, event.PhaseCorrelationImagePublishEvent)

		## peak finding
		print 'peak finding'
		self.peakfinder.setImage(pcimage)
		self.peakfinder.subpixelPeak()
		peak = self.peakfinder.getResults()
		peakvalue = peak['subpixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
		shiftinfo.update({'shift': shift, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2)})
		return shiftinfo


	### some of this should be put directly in Correlator 
	### maybe have phaseCorrelate check validity of its result
	def validateShift(self, shiftinfo):
		'''
		Calculate the validity of an image correlation
		Reasons for rejection:
		  - image shift too large to measure with given image size
		        results in poor correlation
		  - pixel shift too small to use as calibration data
		  	results in good correlation, but reject anyway
		'''
		shift = shiftinfo['shift']
		## Jim is proud of coming up with this ingenious method
		## of calculating a hypotenuse without importing math.
		## It's definietly too late to be working on a Friday.
		totalshift = abs(shift[0] * 1j + shift[1])
		print 'totalshift', totalshift
		peakvalue = shiftinfo['peak value']
		shape = shiftinfo['shape']
		stats = shiftinfo['stats']

		validshiftdict = self.validshift.get()
		print 'validshiftdict', validshiftdict

		## for now I am ignoring percent, only using pixel
		validshift = validshiftdict['calibration']
		print 'validshift', validshift

		## check if shift too small
		if (totalshift < validshift['min']):
			return 'small'
		elif (totalshift > validshift['max']):
			return 'big'
		else:
			return 'good'

	def inRange(self, value, r):
		if (len(r) != 2) or (r[0] > r[1]):
			raise ValueError
		if (value >= r[0]) and (value <= r[1]):
			return True
		else:
			return False

	def correlate(self, image):
		# might also want to normalize with an autocorrelation of 
		# image 0, this might remove effects of poor gain normalization
		# but might also remove the correct peak for small shifts
		self.correlator.setImage(1, image)
		## phase correlation with new image
		try:
			pcimage = self.correlator.phaseCorrelate()
			#imagedata = data.ImageData(self.ID(), pcimage)
			#self.publish(imagedata, event.ImagePublishEvent)
		except correlator.MissingImageError:
			print 'missing image, no correlation'
			return

		## find peak in correlation image
		self.peakfinder.setImage(pcimage)
		peak = self.peakfinder.pixelPeak()
		peak = self.peakfinder.subpixelPeak()
		peak = self.peakfinder.getResults()
		print 'peak', peak
		peakvalue = peak['pixel peak value']
		print 'peak value', peakvalue
		## interpret as a shift
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
		print 'shift', shift
		return {'shift': {'x': shift[1], 'y': shift[0]}, 'peak value': peakvalue}

	def save(self, filename):
		print "saving", self.calibration, "to file:", filename
		try:
			f = file(filename, 'w')
			cPickle.dump(self.calibration, f)
			f.close()
		except:
			print "Error: failed to save calibration"
		return ''

	def load(self, filename):
		try:
			f = file(filename, 'r')
			self.calibration = cPickle.load(f)
			f.close()
		except:
			print "Error: failed to load calibration"
		else:
			print "loading", self.calibration, "from file:", filename
		return ''

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		#### parameters for user to set
		self.attempts = 5
		self.range = [1e-7, 1e-6]
		self.correlationthreshold = 0.05
		self.camerastate = {'size': 512, 'binning': 1, 'exposure time': 500}
		try:
			isdata = self.researchByDataID(self.parameter)
			self.base = isdata.content[self.parameter]
		except:
			self.base = {'x': 0.0, 'y':0.0}
		####

		cspec = self.registerUIMethod(self.uiCalibrate, 'Calibrate', ())

		paramchoices = self.registerUIData('paramdata', 'array', default=('image shift', 'stage position'))


		argspec = (
		self.registerUIData('Base', 'struct', default=self.base),
		self.registerUIData('Minimum', 'float', default=self.range[0]),
		self.registerUIData('Maximum', 'float', default=self.range[1]),
		self.registerUIData('Attempts', 'integer', default=self.attempts),
		self.registerUIData('Correlation Threshold', 'integer', default=self.correlationthreshold),
		self.registerUIData('Camera State', 'struct', default=self.camerastate)
		)
		rspec = self.registerUIMethod(self.uiSetParameters, 'Set Parameters', argspec)

		self.validshift = self.registerUIData('Valid Shift', 'struct', permissions='rw')
		self.validshift.set(
			{
			'correlation': {'min': 20.0, 'max': 200.0},
			'calibration': {'min': 20.0, 'max': 200.0}
			}
		)

		argspec = (self.registerUIData('Filename', 'string'),)
		save = self.registerUIMethod(self.save, 'Save', argspec)
		load = self.registerUIMethod(self.load, 'Load', argspec)

		filespec = self.registerUIContainer('File', (save, load))

		self.registerUISpec('Calibration', (nodespec, cspec, rspec, self.validshift, filespec))

	def uiCalibrate(self):
		self.calibrate()
		return ''

	def uiSetParameters(self, base, r0, r1, a, ct, cs):
		self.base = base
		self.range[0] = r0
		self.range[1] = r1
		self.attempts = a
		self.correlationthreshold = ct
		self.camerastate = cs
		return ''


## this is a base class for simple pixel calibrations 
# for lack of a better name...
class SimpleCalibration(Calibration):
	def __init__(self, id, nodelocations, parameter):
		#self.calibration = {"x pixel shift": {'x': 1.0, 'y': 2.0, 'value': 1.0},
		#					 "y pixel shift": {'x': 3.0, 'y': 4.0, 'value': 1.0}}
		#self.pixelShift(event.ImageShiftPixelShiftEvent(-1, {'row': 2.0, 'column': 2.0}))
		#return

		if parameter not in ('image shift','stage position'):
			raise RuntimeError('parameter %s not supported' % (parameter,) )
		self.parameter = parameter

		Calibration.__init__(self, id, nodelocations)
		self.addEventInput(event.PixelShiftEvent, self.pixelShift)
		self.start()

	def main(self):
		pass
		#self.interact()

	def state(self, value, axis):
		return {self.parameter: {axis: value}}

	def pixelShift(self, ievent):
		print 'PIXELSHIFT'
		print 'calibration =', self.calibration
		print 'pixel shift =', ievent.content
		delta_row = ievent.content['row']
		delta_col = ievent.content['column']
		### someday, this must calculate a mag dependent calibration
		#delta_mag = ievent.content['magnification']

		matrix = self.calibration2matrix()
		print "%s calibration matrix = %s" % (self.parameter, matrix)
		determinant = LinearAlgebra.determinant(matrix)
		deltax = (matrix[1,1] * delta_col -
							matrix[1,0] * delta_row) / determinant
		deltay = (matrix[0,0] * delta_row -
							matrix[0,1] * delta_col) / determinant

		print "calculated %s change = %s, %s" %  (self.parameter, deltax, deltay)
		current = self.researchByDataID(self.parameter)
		currentx = current.content[self.parameter]['x']
		currenty = current.content[self.parameter]['y']
		print "current %s = %s" % (self.parameter, current)
		newimageshift = {self.parameter:
			{
				'x': currentx + deltax,
				'y': currenty + deltay
			}
		}

		imageshiftdata = data.EMData('scope', newimageshift)
		self.publishRemote(imageshiftdata)

	def calibration2matrix(self):
		matrix = Numeric.array([[self.calibration['x pixel shift']['x'],
														self.calibration['x pixel shift']['y']],
													[self.calibration['y pixel shift']['x'],
														self.calibration['y pixel shift']['y']]])
		matrix[0] /= self.calibration['x pixel shift']['value']
		matrix[1] /= self.calibration['y pixel shift']['value']
		return matrix

class ImageShiftCalibration(SimpleCalibration):
	def __init__(self, id, nodelocations):
		param='image shift'
		SimpleCalibration.__init__(self, id, nodelocations, parameter=param)


class StageShiftCalibration(SimpleCalibration):
	def __init__(self, id, nodelocations):
		param='stage position'
		SimpleCalibration.__init__(self, id, nodelocations, parameter=param)

