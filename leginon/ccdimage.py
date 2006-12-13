#!/usr/bin/env python
import numarray
import numarray.nd_image
import numarray.image
import numarray.ma


def combineImages(images, reject=None):
	'''
	Creates an average image from a stack of images.
	reject - specifies outlier rejection threshold
	'''
	# if a list of images was give, convert to
	if type(images) is not numarray.ArrayType:
		images = imageSequenceToArray(images)
	if reject is None:
		# no mask
		maskedimages = images
	else:
		# calculate std. dev. through stack
		if len(images) > 10:
			std = stdev1(images)
		else:
			std = stdev2(images)

		# calculate median through stack
		med = numarray.image.median(images)

		# outliers deviate from the median by too much
		outliers = numarray.abs(images-med) > (reject * std)
		maskedimages = numarray.ma.masked_array(images, mask=outliers)

	avg = numarray.ma.average(maskedimages)
	return numarray.asarray(avg)

def stdev1(images):
	'''better for a large number of images'''
	# calculate standard deviation through stack
	# this is a lot of work but it's the only way I could think of
	# without writing my own function in C print 'ccc'
	shape = images[0].shape
	labels = numarray.arange(shape[0]*shape[1])
	labels.shape = shape
	labels = imageSequenceToArray([labels for i in images])
	std = numarray.nd_image.standard_deviation(images, labels, labels[0])
	std = numarray.array(std,shape=shape, type=numarray.Float32)
	return std

def stdev2(images):
	'''better for a small number of images'''
	mean = numarray.image.average(images)
	return numarray.sqrt(numarray.sum(numarray.power(images-mean,2))/(images.shape[0]-1))
	#.astype(numarray.Float32)

def imageSequenceToArray(images):
	'''
	Takes a sequence (list or tuple) of images and creates a 
	3-dimensional image stack.
	For some reason this is a lot faster than just calling
	numarray.array(imagelist).  Maybe it uses more memory or something.
	'''
	shape = (len(images),) + images[0].shape
	a = numarray.zeros(shape, type=images[0].type())
	for i,im in enumerate(images):
		a[i] = im
	return a


class CCDImageCorrector(object):
	def __init__(self):
		self.references = {}

	def key(self, type, shape, offset, binning):
		'''
		Creates a dictionary key for a reference image
			shape - a shape tuple
			offset - tuple, representing unbinned offset from corner of CCD
			binning - the binning factor
		'''
		key = (type,) + shape + offset + (binning,)
		return key

	def setReference(self, image, type, offset, binning):
		'''
		Assigns a reference image to this object.
			image - image to be added
			type - must be one of: bias, dark, gain
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

	def createGain(self, brights, exptimes, offset, binning):
		'''
		Creates a gain image from a series of bright images
		'''
		gainseries = []
		for i, bright in enumerate(brights):
			exptime = exptimes[i]
			bright = self.correctBias(bright, offset, binning)
			bright = self.correctDark(bright, offset, binning, exptime)
			avg = bright.mean()
			gain = avg / bright
			gainseries.append(avg/bright)
		gain = combineImages(gainseries, reject=3.0)
		self.setReference(gain, 'gain', offset, binning)

	def correctBias(self, input, offset, binning):
		bias = self.getReference('bias', offset, binning, input.shape)
		return input - bias

	def correctDark(self, input, offset, binning, exptime):
		dark = self.getReference('dark', offset, binning, input.shape)
		return input - exptime * dark

	def correctGain(self, input, offset, binning):
		gain = self.getReference('gain', offset, binning, input.shape)
		return gain * input

	def correctBiasDarkGain(self, input, offset, binning, exptime):
		input = self.correctBias(input, offset, binning)
		input = self.correctDark(input, offset, binning, exptime)
		output = self.correctGain(input, offset, binning)
		return output


################## SELF TEST ######################
if __name__ == '__main__':
	import numarray.random_array

	def randomImage(shape, mean, std):
		im = numarray.random_array.normal(mean, std, shape) 
		return im.astype(numarray.Float32)

	shape = 4,4

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

	# fake gain
	exptimes = [1,2,3]
	# add fake bias into fake darks
	bias = c.getReference('bias', (0,0), 2, shape)
	dark = c.getReference('dark', (0,0), 2, shape)
	gain = numarray.arange(shape[0]*shape[1], shape=shape,type=numarray.Float32)
	gain = gain / numarray.nd_image.mean(gain)
	gains = [bias + exptime * dark + exptime * 1000 * gain for exptime in exptimes]
	c.createGain(gains, exptimes, (0,0), 2)

	print c.references

	# fake raw image
	im = randomImage(shape, 5000, 100)
	im = c.correctBiasDarkGain(im, (0,0), 2, 5)
