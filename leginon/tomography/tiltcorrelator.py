import math
import numpy
import scipy.ndimage

from pyami import correlator, peakfinder, imagefun

import leginon.leginondata

import leginon.tiltcorrector


def hanning(size):
	border = size >> 5
	def function(m, n):
		m = abs(m - (size - 1)/2.0) - ((size + 1)/2.0 - border)
		n = abs(n - (size - 1)/2.0) - ((size + 1)/2.0 - border)
		v = numpy.where(m > n, m, n)
		v = numpy.where(v > 0, v, 0)
		return 0.5*(1 - numpy.cos(numpy.pi*v/border - numpy.pi))
	return numpy.fromfunction(function, (size, size))

class Correlator(object):
	def __init__(self, node, tilt_axis, correlation_binning=1,lpf=None):
		self.correlation = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder(lpf)
		self.node = node
		self.tiltcorrector = leginon.tiltcorrector.VirtualStageTilter(self.node)
		self.reset()
		self.setCorrelationBinning(correlation_binning)
		self.hanning = None
		self.channel = None

	def getChannel(self):
		if self.channel is None or self.channel == 1:
			return 0
		else:
			return 1

	def getCorrelationBinning(self):
		return self.correlation_binning

	def setCorrelationBinning(self, correlation_binning):
		self.correlation_binning = correlation_binning

	def setTiltAxis(self, tilt_axis):
		pass

	def reset(self):
		self.shift = {'x':0.0, 'y':0.0}
		self.raw_shift = {'x':0.0, 'y':0.0}
		self.correlation.clearBuffer()

	def peak2shift(self, peak, shape):
		shift = list(peak)
		half = shape[0] / 2.0, shape[1] / 2.0
		if peak[0] > half[0]:
			shift[0] = peak[0] - shape[0]
		if peak[1] > half[1]:
			shift[1] = peak[1] - shape[1]
		return tuple(shift)

	def swapQuadrants(self, image):
		return imagefun.swap_quadrants(image)

	def getCenterSquareImage(self, array):
		shape = array.shape
		if shape[0] == shape[1] and (shape[0] % int(self.correlation_binning)) == 0:
			return array
		minsize = min(shape)
		worksize = (min(shape) / int(self.correlation_binning)) * self.correlation_binning
		offsety = (shape[0] - worksize) / 2
		endy = offsety + worksize
		offsetx = (shape[1] - worksize) / 2
		endx = offsetx + worksize
		return array[offsety:endy,offsetx:endx]

	def correlate(self, imagedata, tiltcorrection=True, channel=None,wiener=False,taper=0,corrtype='phase'):
		image = self.getCenterSquareImage(imagedata['image'])
		if len(image.shape) != 2 or image.shape[0] != image.shape[1]:
			raise ValueError

		if self.correlation_binning != 1:
			image = imagefun.bin(image, int(self.correlation_binning))
		# create new imagedata according to the additional bin
		camdata = leginon.leginondata.CameraEMData(initializer =imagedata['camera'])
		camdata['binning'] = {'x':camdata['binning']['x']*self.correlation_binning, 'y':camdata['binning']['y']*self.correlation_binning}
		newimagedata = leginon.leginondata.AcquisitionImageData(initializer=imagedata)
		newimagedata['camera']=camdata
		# numpy 2.0 does not allow inplace assignment involving different kinds
		# convert to float first
		image = image.astype(numpy.float)
		mean = image.mean()
		image -= mean

		if self.hanning is None or image.shape[0] != self.hanning.shape[0]:
			self.hanning = hanning(image.shape[0])
		image *= self.hanning
		newimagedata['image'] = image
		if tiltcorrection:
			# stage tilt corrector stretchs and updates the image in imagedata according to its stage matrix calibration
			self.tiltcorrector.undo_tilt(newimagedata)
		image = newimagedata['image']
		if taper > 0:
			taperboundary = int((image.shape)[0]*taper*0.01)
			imagefun.taper(image,taperboundary)
		self.correlation.insertImage(image)
		self.channel = channel
		if corrtype == 'phase':
			try:
				pc = self.correlation.phaseCorrelate(zero=True,wiener=wiener)
			except correlator.MissingImageError:
				return
		else:
			try:
				pc = self.correlation.crossCorrelate()
			except correlator.MissingImageError:
				return

		peak = self.peakfinder.subpixelPeak(newimage=pc)
		rows, columns = self.peak2shift(peak, pc.shape) 
		self.raw_shift = {'x': columns, 'y': rows}
		
		self.shift['x'] -= self.raw_shift['x']*self.correlation_binning
		self.shift['y'] += self.raw_shift['y']*self.correlation_binning
		pc = self.swapQuadrants(pc)

		return pc

	def getShift(self, raw):
		if raw:
			shift = self.raw_shift.copy()
		else:
			shift = self.shift.copy()
		return shift

	def tiltShift(self,tilt,shift,angle_from_y=0.0):
		'''
		Correct shift from what tilt corrector gives. It should consider both
		tilt and delta tilt.
		'''
		# got better result if not correct than correct it wrongly.  Leave it uncorrected
		# for now.
		return shift

if __name__ == '__main__':
	import numpy as n
	import pdb
	import matplotlib.pyplot as plt
	import cPickle as pickle
	from pyami import correlator, peakfinder, imagefun

	import leginon.leginondata
	import leginon.tiltcorrector
		
	stagematrix = pickle.load(open('stagematrix_f20_62000','rb'))
	inverse_matrix = numpy.linalg.inv(stagematrix)

	
	def calcBinning(origsize, min_newsize, max_newsize):
		## new size can be bigger than origsize, no binning needed
		if max_newsize >= origsize:
			return 1
		## try to find binning that will make new image size <= newsize
		bin = origsize / max_newsize
		remain = origsize % max_newsize
		while remain:
			bin += 1
			remain = origsize % bin
			newsize = float(origsize) / bin
			if newsize < min_newsize:
				return None
		return bin
	
	imgs = pickle.load(open('imgs_1.p','rb'))
	lpf = 1.5
	# bin down images for correlation
	imageshape = imgs[0]['image'].shape
	# use minsize since tiltcorrelator needs it square, will crop the image in there.
	minsize = min((imageshape[0],imageshape[1]))
	if minsize > 512:
		correlation_bin = calcBinning(minsize, 256, 512)
	else:
		correlation_bin = 1
	if correlation_bin is None:
		# use a non-dividable number and crop in the correlator
		correlation_bin = int(math.ceil(minsize / 512.0))
	
	correlator_ = Correlator(None, None, correlation_bin, lpf)
	
	for img in imgs:
		correlation_image = correlator_.correlate(img, \
			True, channel=0, wiener=False, taper=0,corrtype='phase')												
		raw_correlation = correlator_.getShift(True)						# get raw correlation
		correlation = correlator_.getShift(False)
		print "correlation x: %f, y: %f" %(correlation['x'],correlation['y'])
	
	im_0 = correlator_.correlation.buffer[0]['fft']
	im_1 = correlator_.correlation.buffer[1]['fft']

	correlator_.reset()
	correlator_.correlate(imgs[0], \
				True, channel=0, wiener=False, taper=0,corrtype='phase')
	correlator_.correlate(imgs[4], \
				True, channel=0, wiener=False, taper=0,corrtype='phase')
				
	#correlation_image = correlator_.correlate(imgs[-1], \
	#			True, channel=0, wiener=False, taper=0,corrtype='phase')
	
	correlation = correlator_.getShift(False)
	print "correlation x: %f, y: %f" %(correlation['x'],correlation['y'])

