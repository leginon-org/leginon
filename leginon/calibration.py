import node
import data
import fftengine
import correlator
import peakfinder
import sys

False=0
True=1

class Calibration(node.Node):
	def __init__(self, id, managerlocation):
		node.Node.__init__(self, id, managerlocation)
		self.camerastate = {"offset": {'x': 0, 'y': 0}, \
												"dimension": {'x': 512, 'y': 512}, \
												"binning": {'x': 1, 'y': 1}, \
												"exposure time" : 500}

		if sys.platform == 'win32':
			ffteng = fftengine.fftNumeric()
		else:
			ffteng = fftengine.fftFFTW(planshapes=(), estimate=1)
		self.correlator = correlator.Correlator(ffteng)
		self.peakfinder = peakfinder.PeakFinder()

		self.attempts = 5
		self.range = [0.000, 0.01]
		self.validpixelshift = {'x': [self.camerastate['dimension']['x']/6,
															5*self.camerastate['dimension']['x']/6],
														'y': [self.camerastate['dimension']['y']/6,
															5*self.camerastate['dimension']['y']/6]}

		self.start()

	def main(self):
		pass

	def setting(self, i):
		return {'image shift': {'x': self.settingValue(i)}}

	def settingValue(self, i):
		return ((self.range[1] - self.range[0]) / self.attempts * i) + self.range[0]

	def calibrate(self, EMnodeid):
		self.publishRemote(EMnodeid, data.EMData(self.ID(), self.camerastate))
		self.publishRemote(EMnodeid, data.EMData(self.ID(), self.setting(0)))
		self.image1 = self.researchByDataID('image data').content['image data']
		self.correlator.setImage(0, self.image1)
		for i in range(1, self.attempts):
			self.publishRemote(EMnodeid, data.EMData(self.ID(), self.setting(i)))
			self.image2 = self.researchByDataID('image data').content['image data']
			cdata = self.correlate(self.image2)
			if self.valid(cdata):
				print "good", self.calculate(cdata, i)
				self.correlator.clearBuffer()
				return self.calculate(cdata, i)

	def calculate(self, cdata, i):
		return {'image shift': {'x': cdata['shift']['x'] / self.settingValue(i),
														'y': cdata['shift']['y'] / self.settingValue(i)}}

	def valid(self, cdata):
		if (self.inRange(abs(cdata['shift']['x']), self.validpixelshift['x']) or
				self.inRange(abs(cdata['shift']['y']), self.validpixelshift['y'])):
			return True
		else:
			return False

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
		except correlator.MissingImageError:
			print 'missing image, no correlation'
			return

		## find peak in correlation image
		peak = self.peakfinder.subpixelPeak(npix=3, newimage=pcimage)
		print 'peak', peak
		peakvalue = pcimage[int(peak[0]), int(peak[1])]
		print 'peak value', peakvalue
		## interpret as a shift
		shift = correlator.wrap_coord(peak, pcimage.shape)
		print 'shift', shift
		return {'shift': {'x': shift[1], 'y': shift[0]}}

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)
		self.registerUISpec('Calibration', (nodespec))

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

