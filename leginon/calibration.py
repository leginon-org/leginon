import node
import data
import fftengine
import correlator
import peakfinder
import sys
import event
import time

False=0
True=1

class Calibration(node.Node):
	def __init__(self, id, managerlocation):
		self.camerastate = {"offset": {'x': 0, 'y': 0}, \
												"dimension": {'x': 512, 'y': 512}, \
												"binning": {'x': 1, 'y': 1}, \
												"exposure time" : 500}

		ffteng = fftengine.fftNumeric()
		#if sys.platform == 'win32':
		#	ffteng = fftengine.fftNumeric()
		#else:
		#	ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()

		#### parameters for user to set
		self.emnode = 'em'
		self.attempts = 5
		self.range = [0.0000001, 0.00001]
		####

		# correlation maybe goes into a different node
		self.validshift = \
			{'correlation':
				{'pixel':
					{'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}},
				'percent':
					{'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}}},
			'calibration':
				{'pixel':
					{'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}},
				'percent':
					{'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}}}}

		self.validShiftCallback(
			{'correlation':
				{'pixel':
					{'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}},
				'percent':
					{'x': {'min': 10.0, 'max': 50.0}, 'y': {'min': 10.0, 'max': 50.0}}},
			'calibration':
				{'pixel':
					{'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}},
				'percent':
					{'x': {'min': 10.0, 'max': 50.0}, 'y': {'min': 10.0, 'max': 50.0}}}})

		self.correlationthreshold = 0.05
		# asdf
		self.axislist = ['x', 'y']

		node.Node.__init__(self, id, managerlocation)
		self.clearStateImages()
		self.start()

	def validShiftCallback(self, value=None):
		if value:
			updatelist = []
			for shift in self.validshift:
				if self.validshift[shift] != value[shift]:
					updatelist.append(shift)

			for shift in updatelist:
				typelist = []
				for t in self.validshift[shift]:
					if self.validshift[shift][t] != value[shift][t]:
						typelist.append(t)
				if len(typelist) != 1:
					break
				for t in typelist:
					self.validshift[shift][t] = value[shift][t]
					if t == 'percent':
						self.validshift[shift]['pixel'] = \
							self.calculatePixelFromPercent(value[shift][t])
					elif t == 'pixel':
						value[shift]['percent'] = \
							self.calculatePercentFromPixel(value[shift][t])
		else:
			return self.validshift

	def calculatePixelFromPercent(self, percent):
		pixel = {'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}}
		for axis in percent:
			for limit in percent[axis]:
				pixel[axis][limit] = self.camerastate['dimension'][axis] \
						* percent[axis][limit]/100
		return pixel

	def calculatePercentFromPixel(self, pixel):
		percent = {'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}}
		for axis in pixel:
			for limit in pixel[axis]:
				percent[axis][limit] = \
					pixel[axis][limit] / self.camerastate['dimension'][axis] * 100
		return percent

	def main(self):
		pass

	def state(self, value):
		raise NotImplementedError()

	def calibrate(self):
		self.clearStateImages()

		adjustedrange = self.range
		print 'publishing camera state', self.emnode
		camdata = data.EMData(self.ID(), self.camerastate)
		print 'camdata', camdata
		self.publishRemote(self.emnode, camdata)

		print 'hello again from calibrate'

		# might reuse value from previous axis
		for axis in self.axislist:
			for i in range(self.attempts):
				value = (adjustedrange[1] - adjustedrange[0]) / 2 + adjustedrange[0]

				state1 = self.state(0.0, axis)
				state2 = self.state(value, axis)
				print 'states', state1, state2
				shiftinfo = self.measureStateShift(state1, state2)
				print 'shiftinfo', shiftinfo

				verdict = self.validateShift(shiftinfo)

				if verdict == 'good':
					print "good", self.calculate(cdata, value) 
					self.publishRemote(self.emnode, data.EMData(self.ID(), self.state(0.0, axis)))
					return self.calculate(cdata, value)
				elif verdict == 'small shift':
					print "too small"
					adjustedrange[0] = value
				elif verdict == 'big shift':
					print "too big"
					adjustedrange[1] = value
				else:
					raise RuntimeError('hung jury')

		self.publishRemote(self.emnode, data.EMData(self.ID(), self.state(0.0, axis)))

	def clearStateImages(self):
		self.images = []

	def acquireStateImage(self, state):
		## determine if this state is already acquired
		for info in self.images:
			if info['state'] == state:
				image = info['image']
				return info

		## acquire image at this state
		print 'setting state', state
		emdata = data.EMData(self.ID(), state)
		print 'publishing state', self.emnode, emdata
		self.publishRemote(self.emnode, emdata)
		print 'sleeping 1 sec'
		time.sleep(1.0)
		print 'getting image data'
		imagedata = self.researchByDataID('image data')
		print 'imagedata type', type(imagedata)
		image = imagedata.content['image data']

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

		## phase correlation
		print 'inserting into correlator'
		self.correlator.setImage(0, image1)
		self.correlator.setImage(1, image2)
		print 'correlation'
		pcimage = self.correlator.phaseCorrelate()

		## peak finding
		print 'peak finding'
		self.peakfinder.setImage(pcimage)
		self.peakfinder.subpixelPeak()
		peak = self.peakfinder.getResults()
		peakvalue = peak['pixel peak value']
		shift = correlator.wrap_coord(peak['subpixel peak'], pcimage.shape)
		shiftinfo = {'shift': shift, 'peak value': peakvalue, 'shape':pcimage.shape, 'stats': (stats1, stats2)}
		return shiftinfo

	def calculate(self, cdata, value):
		return {'image shift': {'x': cdata['shift']['x'] / value,
			'y': cdata['shift']['y'] / value}}


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
		shift = shiftinfo['image shift']
		## Jim is proud of coming up with this ingenious method
		## of calculating a hypotenuse without importing math.
		## It's definietly too late to be working on a Friday.
		totalshift = abs(shift[0] * 1j + shift[1])
		peakvalue = shiftinfo['peak value']
		shape = shiftinfo['shape']
		stats = shiftinfo['stats']

		## judge based on image stats
		## this should probably be done even before doing a 
		## correlation to save time.  should reject doing doing
		## a calibration over a big black area and stuff like that
		## check that stats[0] is similar to stats[1]
		# 

		## judge based on correlation peak value
		if peakvalue < minpeakvalue:
			peakverdict = 'low'
		elif peakvalue > maxpeakvalue:
			peakverdict = 'high'
		else:
			peakverdict = 'normal'

		### Is this right?:
		### We care about shift on each axis when it comes
		### to validating the accuracy of the correlation.
		### We care about total shift distance when it comes 
		### to getting a good calibration, regardless of direction.

		validshift = []
		for dim in (0,1):
			minshift = shape[dim] / 10.0
			maxshift = 5.0 * shape[dim] / 10.0
			validshift.append( (minshift,maxshift) )

		if (self.inRange(abs(shift[0]), validshift[0]) and
			self.inRange(abs(shift[1]), validshift[1])):


			if shiftinfo['peak value'] > self.correlationthreshold:
				verdict = 'good'
			else:
				if cdata['peak value'] > self.correlationthreshold * 2:
					verdict = 'small shift'
				else:
					verdict = 'big shift'

		return verdict

	def inRange(self, value, r):
		if (len(r) != 2) or (r[0] > r[1]):
			raise ValueError
		if (value >= r[0]) and (value <= r[1]):
			return True
		else:
			return False

	def correlate(self, image):
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

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		cspec = self.registerUIMethod(self.uiCalibrate, 'Calibrate', ())

		paramchoices = self.registerUIData('paramdata', 'array', default=('image shift', 'stage position'))

		argspec = (
		self.registerUIData('EM Node', 'string', default='em'),
		self.registerUIData('Minimum', 'float', default=self.range[0]),
		self.registerUIData('Maximum', 'float', default=self.range[1]),
		self.registerUIData('Attempts', 'integer', default=self.attempts),
		self.registerUIData('Correlation Threshold', 'integer', default=self.correlationthreshold),
		self.registerUIData('Camera State', 'struct', default=self.camerastate)
		)
		rspec = self.registerUIMethod(self.uiSetParameters, 'Set Parameters', argspec)

		vspec = self.registerUIData('Valid Shift', 'struct', permissions='rw')
		vspec.set(self.validShiftCallback)

		self.registerUISpec('Calibration', (nodespec, cspec, rspec, vspec))

	def uiCalibrate(self):
		self.calibrate()
		return ''

	def uiSetParameters(self, emnode, r0, r1, a, ct, cs):
		self.emnode = ('manager', emnode)
		self.range[0] = r0
		self.range[1] = r1
		self.attempts = a
		self.correlationthreshold = ct
		self.camerastate = cs
		# update valid somehow
		#self.validShiftCallback(self.validshift)
		return ''


class StageCalibration(Calibration):
	def __init__(self, id, managerlocation):
		Calibration.__init__(self, id, managerlocation)

	def state(self, value, axis):
		return {'stage position': {axis: value}}


class ImageShiftCalibration(Calibration):
	def __init__(self, id, managerlocation):
		Calibration.__init__(self, id, managerlocation)

	def state(self, value, axis):
		return {'image shift': {axis: value}}


class AutoFocusCalibration(Calibration):
	def __init__(self, id, managerlocation):
		Calibration.__init__(self, id, managerlocation)

	def state(self, value, axis):
		return {'beam tilt': {axis: value}}

