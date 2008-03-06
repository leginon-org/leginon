#!/usr/bin/env python
'''
Classes for managing image corrections (bias, flat, dark) on CCD images
'''

### turn debugging output on/off
debug = False

import numpy
numfloat = numpy.float32
imagemean = numpy.mean
imagestd = numpy.std
randomarray = numpy.random
median = numpy.median

class CorrectorError(RuntimeError):
	pass

class Accumulator(object):
	'''
An Accumulator object keeps track of the mean image
on a sequence of images without having to keep that series of images
in memory.  The stats are updated whenever a new image is inserted
into the series.

Usage:
    a = Accumulator()
      by default, the accumulator is only calculating the mean image,
      not the standard deviation.  If you want to be able to get the
      standard deviation image, then create your object like this:
    a = Accumulator(std=True)
		
    a = Accumulator(medsize=???)
      medsize is the size of the median image buffer.  This is an
      experimental technique of avoiding outlier pixels from
      cosmic rays or whatever.  

a = Accumulator(std=True)

Available methods on you accumulator object:
    mean() - this returns the combined mean of the series
    std() - returns the combined standard deviation of the series
             (only available if accumulator was initialized with std=True)
    reset() - resets the accumulator, as if it was just initialized

	'''
	def __init__(self, std=False, medsize=0):
		self.reset(std, medsize)

	def reset(self, calcstd=False, medsize=0):
		self.__n = 0
		self.__mean = None
		self.__sum2 = None
		self.__std = None
		self.__calcstd = calcstd
		self.__medbuffer = []
		self.__medsize = medsize
		self.lock = False

	def resetMedian(self):
		self.__medbuffer = []
		self.lock = True

	def insertMedian(self, image):
		if debug:
			print 'inserting into median buffer'
		if len(self.__medbuffer) == self.__medsize:
			del self.__medbuffer[0]

		self.__medbuffer.append(image)

		if len(self.__medbuffer) == self.__medsize:
			if debug:
				print 'calculating median'
			return median(self.__medbuffer)
		else:
			return None

	def insert(self, x):
		if self.lock:
			raise RuntimeError('Median buffer was reset.  Reset the Accumulator before insert')
		if self.__medsize:
			x = self.insertMedian(x)
		if x is None:
			return

		if debug:
			print 'doing calculations'
		self.__std = None
		self.__n += 1
		if self.__n == 1:
			self.__mean = numpy.asarray(x, numfloat)
			if self.__calcstd:
				self.__sum2 = numpy.zeros(self.__mean.shape, numfloat)
		else:
			delta = x - self.__mean
			self.__mean = self.__mean + delta / self.__n
			if self.__calcstd:
				self.__sum2 = self.__sum2 + delta * (x - self.__mean)
		if debug:
			print 'done calculations'

	def mean(self):
		return self.__mean

	def std(self):
		if self.__n == 0:
			return None
		if self.__std is None and self.__calcstd:
			self.__std = numpy.sqrt(self.__sum2 / self.__n)
		return self.__std

def testAccumulator():
	a = Accumulator(True)
	b = []
	for i in range(4):
		im = i * numpy.ones((4,4), numfloat)
		print i
		print im
		a.insert(im)
		b.append(im)
	print 'Traditional:'
	print '  mean:', imagemean(b,0)
	print '  std:', imagestd(b,0)
	print 'Accumulator:'
	print '  mean:', a.mean()
	print '  std:', a.std()

class CorrectorBase(object):
	'''
Base class for Corrector.  This defines how to do the image corrections,
like bias correction, dark correction, flat correction, but does not
define how to create the bias, dark, and flat images.
You should create a subclass that defines the methods bias(), dark(), 
and flat() to return the image.  For instance, these methods could
read the image from a database.
	'''
	def bias(self):
		raise NotImplementedError('bias method needs to return a bias image')

	def dark(self):
		raise NotImplementedError('dark method needs to return a dark image')

	def flat(self):
		raise NotImplementedError('flat method needs to return a flat image')

	def correctBias(self, input):
		bias = self.bias()
		if bias is None:
			raise CorrectorError('bias image not available')
		return input - bias

	def correctDark(self, input, exptime):
		dark = self.dark()
		if dark is None:
			raise CorrectorError('dark image not available')
		return input - exptime * dark

	def correctFlat(self, input):
		flat = self.flat()
		if flat is None:
			raise CorrectorError('flat image not available')
		flattened = input * flat
		flattened = numpy.where(numpy.isfinite(flattened), flattened, 0)
		return flattened

	def correctBiasDarkFlat(self, input, exptime):
		input = self.correctBias(input)
		input = self.correctDark(input, exptime)
		output = self.correctFlat(input)
		return output


class Corrector(CorrectorBase):
	'''
Implements two methods for creating correction images:
   1. Simply setting the image using setBias, setDark, setFlat.
       Use this if you have already created the images and just
       want to use them in this Corrector object.
   2. Incrementally combining by inserting raw images one by one.
      This uses the Accumulator class.  You can feed it raw images
      using insertBias, insertDark, insertBright.  These only take
      raw images, and will do the appropriate normalizations before feeding
      to the Accumulator.   This means, you do not feed a normalized flat
      image to the insertBright method, just give it a raw bright image.
			Similarly, only give insertDark a raw dark image, not one that
      is already divided by the exposure time.

      You can only use insertDark if you already have created a bias image,
      because internally, it will subtract the bias before adding it to the
      average image.

      You can only use insertBright if you already have a bias and dark image,
      because it needs to subtract them before calculating the average image.
	'''
	def __init__(self, medsize=0):
		self.__accbias = Accumulator(medsize=medsize)
		self.__accdark = Accumulator(medsize=medsize)
		self.__accflat = Accumulator(medsize=medsize)

	def reset(self):
		self.__accbias.reset()
		self.__accdark.reset()
		self.__accflat.reset()

	def bias(self):
		'''return the current bias image'''
		return self.__accbias.mean()

	def dark(self):
		'''return the current dark image'''
		return self.__accdark.mean()

	def flat(self):
		'''return the current flat image'''
		return self.__accflat.mean()

	def setBias(self, bias):
		'''set the current bias image'''
		self.__accbias.reset()
		self.__accbias.insert(bias)

	def setDark(self, dark):
		'''set the current dark image'''
		self.__accdark.reset()
		self.__accdark.insert(dark)

	def setFlat(self, flat):
		'''set the current flat image'''
		self.__accflat.reset()
		self.__accflat.insert(flat)

	def insertBias(self, bias):
		'''
		Add new bias image to the accumlator.
		'''
		self.__accbias.insert(bias)

	def insertDark(self, dark, exptime):
		dark = self.correctBias(dark)
		dark = dark/exptime
		self.__accdark.insert(dark)

	def insertBright(self, bright, exptime):
		bright = self.correctBias(bright)
		bright = self.correctDark(bright, exptime)
		avg = bright.mean()
		flat = avg / bright
		self.__accflat.insert(flat)


################## SELF TEST ######################
if __name__ == '__main__':
	def randomImage(shape, mean, std):
		im = randomarray.normal(mean, std, shape) 
		return im.astype(numfloat)

	shape = 512,512

	c = Corrector()

	# fake bias image
	biases = [randomImage(shape, 400, 40) for i in range(10)]
	#biases[0][2,2] = 100000
	for bias in biases:
		c.insertBias(bias)

	# fake dark image
	exptimes = [1,2,3]
	# add fake bias into fake darks
	bias = c.bias()
	darks = [bias + exptime * randomImage(shape, 10, 1) for exptime in exptimes]
	for dark,exptime in zip(darks,exptimes):
		c.insertDark(dark, exptime)

	# fake flat
	exptimes = [1,2,3]
	# add fake bias into fake darks
	bias = c.bias()
	dark = c.dark()
	flat = 5 * numpy.arange(shape[0]*shape[1], dtype=numfloat)
	flat.shape = shape
	flat = flat / flat.mean()
	flats = [bias + exptime * dark + exptime * 1000 * flat for exptime in exptimes]
	for flat,exptime in zip(flats,exptimes):
		c.insertBright(flat, exptime)

	# fake raw image
	im = randomImage(shape, 5000, 100)
	im = c.correctBiasDarkFlat(im, 2)
