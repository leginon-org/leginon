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
		self.emnode = None
		self.attempts = 5
		self.range = [0.0000001, 0.00001]
		####

		self.validshiftpixel = self.validshiftpercent = \
			{'x': {'min': None, 'max': None}, 'y': {'min': None, 'max': None}}
		self.validShiftPercentCallback(
			{'x': {'min': 10.0, 'max': 50.0}, 'y': {'min': 10.0, 'max': 50.0}})

		self.correlationthreshold = 0.05

		node.Node.__init__(self, id, managerlocation)
		self.clearStateImages()
		self.start()

	def validShiftPixelCallback(self, value=None):
		if value:
			self.validshiftpixel = value
			for axis in self.validshiftpercent:
				for limit in self.validshiftpercent[axis]:
					self.validshiftpercent[axis][limit] = \
						self.validshiftpixel[axis][limit] \
							/ self.camerastate['dimension'][axis] * 100,
		else:
			return self.validshiftpixel

	def validShiftPercentCallback(self, value=None):
		if value:
			self.validshiftpercent = value
			for axis in self.validshiftpixel:
				for limit in self.validshiftpixel[axis]:
					self.validshiftpixel[axis][limit] = \
						self.camerastate['dimension'][axis] \
							* self.validshiftpercent[axis][limit]/100
		else:
			return self.validshiftpercent

	def main(self):
		pass

	def imageshiftState(self, value):
		return {'image shift': {'x': value}}

	def goniometerState(self, value):
		return {'stage position': {'x': value}}

	def calibrate(self):
		self.clearStateImages()

		if self.parameter == 'stage position':
			setting = self.goniometerState
		elif self.parameter == 'image shift':
			setting = self.imageshiftState
		else:
			raise RuntimeError('unknown parameter %s' % self.parameter)

		adjustedrange = self.range
		print 'publishing camera state', self.emnode
		camdata = data.EMData(self.ID(), self.camerastate)
		print 'camdata', camdata
		self.publishRemote(self.emnode, camdata)

		print 'hello again from calibrate'

		for i in range(self.attempts):
			value = (adjustedrange[1] - adjustedrange[0]) / 2 + adjustedrange[0]

			state1 = setting(0.0)
			state2 = setting(value)
			print 'states', state1, state2
			shiftinfo = self.measureStateShift(state1, state2)
			print 'shiftinfo', shiftinfo

			verdict = self.validateShift(shiftinfo)

			if verdict == 'good':
				print "good", self.calculate(cdata, value) 
				self.publishRemote(self.emnode, data.EMData(self.ID(), setting(0.0)))
				return self.calculate(cdata, value)
			elif verdict == 'small shift':
				print "too small"
				adjustedrange[0] = value
			elif verdict == 'big shift':
				print "too big"
				adjustedrange[1] = value
			else:
				raise RuntimeError('hung jury')




		self.publishRemote(self.emnode, data.EMData(self.ID(), setting(0.0)))

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
		self.registerUIData('Parameter', 'string', choices=paramchoices, default='image shift'),
		self.registerUIData('Minimum', 'float', default=self.range[0]),
		self.registerUIData('Maximum', 'float', default=self.range[1]),
		self.registerUIData('Attempts', 'integer', default=self.attempts),
		self.registerUIData('Camera State', 'struct', default=self.camerastate)
		)
		rspec = self.registerUIMethod(self.uiSetParameters, 'Set Parameters', argspec)

		pixelspec = self.registerUIData('Valid Pixel Shift', 'struct', permissions='rw')
		pixelspec.set(self.validShiftPixelCallback)
		percentspec = self.registerUIData('Valid Percent Shift', 'struct', permissions='rw')
		percentspec.set(self.validShiftPercentCallback)

		self.registerUISpec('Calibration', (nodespec, cspec, rspec, pixelspec, percentspec))

	def uiCalibrate(self):
		self.calibrate()
		return ''

	def uiSetParameters(self, emnode, param, r0, r1, a, cs):
		self.emnode = ('manager', emnode)
		self.parameter = param
		self.range[0] = r0
		self.range[1] = r1
		self.attempts = a
		self.camerastate = cs
		self.validShiftPercentCallback(self.validshiftpercent)
		return ''

#			imageshift = (shiftrange[1] + shiftrange[0])/2
#			shiftpair = ((shiftrange[1] + shiftrange[0])/4, \
#										-(shiftrange[1] + shiftrange[0])/4) 
#			statepair = ({'image shift': {'x': shiftpair[0], 'y': 0.0}}, \
#										{'image shift': {'x': shiftpair[1], 'y': 0.0}})
#			imagepair = self.imagePair(EMnodeid, statepair)
#			correlationdata = correlation.correlation(imagepair[0], \
#													imagepair[1], 0, 1, 1)
#			pixelshiftmagnitude = \
#				math.sqrt(correlationdata['phase correlation peak'][0]**2 \
#									+ correlationdata['phase correlation peak'][1]**2)
#
#			if not self.correlates(correlationdata, correlationthreshold):
#				# images don't correlate, need smaller shift
#				shiftrange = (shiftrange[0], imageshift)
#			else: # images correlate, check if pixel shift is good
#				if (pixelshiftmagnitude >= pixelshiftrange[0]) \
#							and (pixelshiftmagnitude <= pixelshiftrange[1]):
#					return {'pixel shift': correlationdata['phase correlation peak'],
#									'image shift': imageshift}
#				elif pixelshiftmagnitude > pixelshiftrange[1]:
#					shiftrange = (shiftrange[0], imageshift)
#				elif pixelshiftmagnitude < pixelshiftrange[0]:
#					shiftrange = (imageshift, shiftrange[1])

#		return None

#	def correlates(self, correlationdata, correlationthreshold):
#		if correlationdata['phase correlation image'][correlationdata['phase correlation index']] > correlationthreshold:
#			return 1
#		else:
#			return 0

#	def imagePair(self, EMnodeid, statepair):
#		self.publishRemote(EMnodeid, data.EMData(self.ID(), statepair[0]))
#		image1 = self.researchByDataID('image data').content['image data']
#		self.publishRemote(EMnodeid, data.EMData(self.ID(), statepair[1]))
#		image2 = self.researchByDataID('image data').content['image data']
#		return (image1, image2)

