#!/usr/bin/env python
'''

'''

import numpy

def combineImages(images, reject=None):
	'''
	Creates an average image from a stack of images.
	reject - specifies outlier rejection threshold
	'''
	# if a list of images was given, convert to 3d array
	images = numpy.asarray(images)

	if reject is None:
		# no mask
		avg = numpy.mean(images, 0)
	else:
		# calculate std. dev. through stack
		std = numpy.std(images, 0)

		# calculate median through stack
		med = numpy.mean(images)

		# outliers deviate from the median by too much
		outliers = numpy.abs(images-med) > (reject * std)
		maskedimages = numpy.ma.masked_array(images, mask=outliers)

		avg = numpy.ma.average(maskedimages, 0)
	return numpy.asarray(avg)

class StackAccumulator(object):
	'''
	A stack accumulator object keeps track of various statistics
	on a stack of images.  The stats are updated whenever a new image
	is inserted into the stack.
	Available stats:
		mean()
		std()
		sum()
	'''
	def __init__(self):
		self.reset()

	def reset(self):
		self.n = 0
		self.mean = None
		self.sum2 = None
		self._std = None

	def insert(self, x):
		self._std = None
		self.n += 1
		if self.n == 0:
			self.mean = numpy.asarray(x, numpy.float)
			self.sum2 = numpy.zeros(self.mean.shape, numpy.float)
		elif self.n == 1:
			delta = x - self.mean
			self.mean = self.mean + delta / self.n
			self.sum2 = delta * (x - self.mean)
		else:
			delta = x - self.mean
			self.mean = self.mean + delta / self.n
			self.sum2 = self.sum2 + delta * (x - self.mean)

	def mean(self):
		return self.mean

	def std(self):
		if self.n == 0:
			raise RuntimeError('no data inserted yet')
		if self._std is None:
			if self.n == 1:
				self._std = numpy.sqrt(self.sum2)
			else:
				self._std = numpy.sqrt(self.sum2 / self.n)
		return self._std

class MedianAccumulator(object):
	def __init__(self):
		self.n = 0
		self.a = None

	def insert(self, x):
		self.n += 1
		x = numpy.asarray(x).reshape(-1)
		if self.n == 1:
			self.a = x
		else:
			self.a = numpy.concatenate((self.a, x))
		print self.a

class Corrector(object):
	def __init__(self):
		self.references = {}

	def key(self, type, shape, offset, binning):
		'''
		Creates a dictionary key for a reference image
			type - one of: 'bias', 'dark', 'flat'
			shape - a shape tuple
			offset - tuple, representing unbinned offset from upper left
				corner of CCD
			binning - the binning factor
		'''
		key = (type,) + shape + offset + binning
		return key

	def setReference(self, image, type, offset, binning):
		'''
		Assigns a reference image to this object.
			image - image to be added
			type - must be one of: bias, dark, flat
		'''
		self.references[self.key(type,image.shape,offset,binning)] = image

	def getReference(self, type, offset, binning, shape):
		try:
			return self.references[self.key(type,shape,offset,binning)]
		except KeyError:
			return None

	def createBias(self, biases, offset, binning):
		'''
		Creates a bias image from a series of acquired images.
		The image must be acquired with 0 exposure time and no exposure
		to light.
		'''
		bias = combineImages(biases, reject=3.0)
		self.setReference(bias, 'bias', offset, binning)

	def createDark(self, darks, exptimes, offset, binning):
		'''
		Creates a dark image from a series of dark images
		'''
		shape = darks[0].shape
		darkseries = []
		for i,dark in enumerate(darks):
			dark = self.correctBias(dark, offset, binning)
			exptime = float(exptimes[i])
			darkseries.append(dark/exptime)
		dark = combineImages(darkseries, reject=3.0)
		self.setReference(dark, 'dark', offset, binning)

	def createFlat(self, brights, exptimes, offset, binning):
		'''
		Creates a flat image from a series of bright images
		'''
		flatseries = []
		for i, bright in enumerate(brights):
			exptime = exptimes[i]
			bright = self.correctBias(bright, offset, binning)
			bright = self.correctDark(bright, offset, binning, exptime)
			avg = bright.mean()
			flat = avg / bright
			flatseries.append(avg/bright)
		flat = combineImages(flatseries, reject=3.0)
		self.setReference(flat, 'flat', offset, binning)

	def correctBias(self, input, offset, binning):
		bias = self.getReference('bias', offset, binning, input.shape)
		return input - bias

	def correctDark(self, input, offset, binning, exptime):
		dark = self.getReference('dark', offset, binning, input.shape)
		return input - exptime * dark

	def correctFlat(self, input, offset, binning):
		flat = self.getReference('flat', offset, binning, input.shape)
		return flat * input

	def correctBiasDarkFlat(self, input, offset, binning, exptime):
		input = self.correctBias(input, offset, binning)
		input = self.correctDark(input, offset, binning, exptime)
		output = self.correctFlat(input, offset, binning)
		return output


################## SELF TEST ######################
if __name__ == '__main__':
	import numpy

	def randomImage(shape, mean, std):
		im = numpy.random.normal(mean, std, shape) 
		return im.astype(numpy.float32)

	shape = 512,512

	c = CCDImageCorrector()

	# fake bias image
	biases = [randomImage(shape, 400, 40) for i in range(10)]
	biases[0][2,2] = 100000
	c.createBias(biases, (0,0), 2)

	# fake dark image
	exptimes = [1,2,3]
	# add fake bias into fake darks
	bias = c.getReference('bias', (0,0), 2, shape)
	darks = [bias + exptime * randomImage(shape, 10, 1) for exptime in exptimes]
	c.createDark(darks, exptimes, (0,0), 2)

	# fake flat
	exptimes = [1,2,3]
	# add fake bias into fake darks
	bias = c.getReference('bias', (0,0), 2, shape)
	dark = c.getReference('dark', (0,0), 2, shape)
	flat = numpy.arange(shape[0]*shape[1], dtype=numpy.float32)
	flat.shape = shape
	flat = flat / flat.mean()
	flats = [bias + exptime * dark + exptime * 1000 * flat for exptime in exptimes]
	c.createFlat(flats, exptimes, (0,0), 2)

	for key,value in c.references.items():
		print key
		print value

	# fake raw image
	im = randomImage(shape, 5000, 100)
	im = c.correctBiasDarkFlat(im, (0,0), 2, 5)
