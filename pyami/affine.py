'''
things that make affine_transform easier
'''

import numpy
import quietscipy
import scipy.ndimage

def affine_transform_offset(inputshape, outputshape, affine_matrix, offset=(0,0)):
	'''
	calculation of affine transform offset
	for now we assume center of image
	'''
	outcenter = numpy.array(outputshape, numpy.float32)
	outcenter.shape = (2,)
	outcenter = outcenter / 2.0 - 0.5
	outcenter += offset

	incenter = numpy.array(inputshape, numpy.float32)
	incenter.shape = (2,)
	incenter = incenter / 2.0 - 0.5

	outcenter2 = numpy.dot(affine_matrix, outcenter)

	offset = incenter - outcenter2
	return offset

class ImageCache(object):
	def __init__(self, maxsize):
		self.cache = newdict.OrderedDict()
		self.maxsize = maxsize
		self.size = 0

	def insert(self, key, image):
		if key in self.cache:
			raise RuntimeError('key already in cache')
		imsize = image.size() * image.itemsize()
		if imsize > self.maxsize:
			print 'image too big for cache'
			return
		newsize = self.size + imsize
		while newsize > self.maxsize:
			self.removeOldest()
			newsize = self.size + imsize

		self.cache[key] = image
		self.size += imsize

	def removeOldest(self):
		try:
			firstkey = self.cache.keys()[0]
		except IndexError:
			return
		im = self.cache[firstkey]
		imsize = im.size() * im.itemsize()
		del self.cache[firstkey]
		self.size -= imsize

	def get(self, key):
		return self.cache[key]

class SplineFilterCache(ImageCache):
	def filter(self, key, image):
		if key not in self.cache:
			spline = scipy.ndimage.spline_filter(image, order=3)
			self.insert(key, spline)
		return self.get(key)

def matrixAngle(mat):
	print numpy.arccos(mat[0,0])
	print numpy.arcsin(-mat[0,1])
	print numpy.arcsin(mat[1,0])
	print numpy.arccos(mat[1,1])

def transform(image2, libcvMatrix, image1shape):
	'''
	libCV.MatchImages returns a matrix representing the transform between
	image1 and image2.  This function will take that matrix and image2
	and transform image2 to look like image1.  Center of resulting image
	should match center of image 1.
	'''
	matrix = numpy.array(libcvMatrix)

	'''
	## add additional shift to use image centers as center of transform
	image2shape = numpy.array(image2.shape)
	image1shape = numpy.array(image1shape)
	off = image1shape/2.0 - image2shape/2.0
	offmat = numpy.identity(3)
	offmat[2,0] = off[0]
	offmat[2,1] = off[1]
	matrix = numpy.matrixmultiply(offmat, matrix)
	'''

	matrix.transpose()
	mat = matrix[:2,:2]
	offset = tuple(matrix[:2,2])
	output = scipy.ndimage.affine_transform(image2, mat, offset=offset, output_shape=image1shape)
	return output
