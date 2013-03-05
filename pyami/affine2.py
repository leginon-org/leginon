#!/usr/bin/env python
'''
things that make affine_transform easier
'''

import numpy
import quietscipy
import scipy.ndimage
import scipy.linalg

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

class Transform3x3(object):
	def __init__(self, matrix):
		self.matrix = matrix

class Translation(Transform3x3):
	def __init__(self, vector):
		matrix = numpy.identity(3)
		matrix[:-1,-1] = vector
		Transform3x3.__init__(self, matrix)

class Rotation(Transform3x3):
	def __init__(self, angle):
		matrix = numpy.identity(3)
		matrix[:2,:2] = numpy.array(((numpy.cos(angle),-numpy.sin(angle)), (numpy.sin(angle), numpy.cos(angle))))
		Transform3x3.__init__(self, matrix)

class Scale(Transform3x3):
	def __init__(self, scale0, scale1=None):
		matrix = numpy.identity(3)
		if scale1 is None:
			scale1 = scale0
		matrix[0,0] = scale0
		matrix[1,1] = scale1
		Transform3x3.__init__(self, matrix)

def matrix_chain(transformations):
	'''
	given a sequence of transforms, calculate a single affine transform matrix
	'''
	matrices = [trans.matrix for trans in transformations]
	matrices.reverse()
	identity = numpy.identity(3)
	final = reduce(numpy.dot, matrices, identity)
	return final

def trs_to_matrix(translation, rotation, scale):
	'''
	Generate an affine transform matrix from the given translation, rotation
	and scale in that order.
	'''
	t = Translation(translation)
	r = Rotation(rotation)
	s = Scale(scale)
	chain = (t,r,s)
	matrix = matrix_chain(chain)
	return matrix

def trs_point(point, translation, rotation, scale):
	p = numpy.ones(3)
	p.shape = 3,1
	p[:2,0] = point
	matrix = trs_to_matrix(translation, rotation, scale)
	newpoint = numpy.dot(matrix, p)[:-1]
	newpoint.shape = 2,
	return newpoint

def trs_transform(input, translation, rotation, scale):
	#matrix = trs_to_matrix(translation, rotation, scale)
	matrix = trs_to_matrix((0,0), rotation, scale)

	print 'FINAL MATRIX', matrix
	imatrix = scipy.linalg.inv(matrix[:2,:2])
	inputshape = (512,512)
	outputshape = (512,512)
	center = 256,256
	point0 = trs_point(center, (0,0), rotation, scale)
	aoffset = translation[0]-point0[0], translation[1]-point0[1]

	#aoffset = affine_transform_offset(inputshape, outputshape, amatrix, aoffset)
	output = scipy.ndimage.affine_transform(input, matrix=imatrix, offset=aoffset)
	return output

def OLDtransform(image2, libcvMatrix, image1shape):
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

def test1():
	import pyami.mrc
	input = pyami.mrc.read('4k-512.mrc')
	rot = 30.0 * numpy.pi / 180.0
	output = trs(input, (20,100), rot, 1.0)
	pyami.mrc.write(output, 'output.mrc')

def test2():
	point = 0,1
	print 'point', point
	newpoint = trs_point(point, (0,0), numpy.pi/2, 1.0)
	print 'newpoint', newpoint

def test3():
	import pyami.mrc
	input = pyami.mrc.read('4k-512.mrc')
	rot = 5.0 * numpy.pi / 180.0
	output = trs_transform(input, (0,0), rot, 1.0)
	pyami.mrc.write(output, 'output.mrc')

def transform(ainput, matrix, **kwargs):
	'''
	Wrapper around scipy.ndimage.affine_transform.  This behaves a little
	better than the original in that you can give it a proper 3x3 transform
	matrix rather than splitting up in to a 2x2 matrix and an offset.  Also,
	the direction of the transorm is more logical.  In the scipy function,
	you actually give it a matrix that transforms from the output to the input,
	rather than the way you think of it:  input to output.
	'''
	imatrix = scipy.linalg.inv(matrix)
	af_matrix = imatrix[:2,:2]
	af_offset = imatrix[:2,2]
	aoutput = scipy.ndimage.affine_transform(ainput, af_matrix, offset=af_offset, **kwargs)
	return aoutput

def transform_centered(ainput, matrix, center, **kwargs):
	'''
	This is like the basic transform() function, but this one will move a
	given coordinate to the center of the image and then treat the center
	of the image as the origin of the transform rather than using 0,0 (the
	upper left corner) as the transform origin.
	'''
	## translate the given center to the 0,0 corner position
	trans1 = Translation((-center[0],-center[1]))

	## do the given matrix transform
	trans2 = Transform3x3(matrix)

	## translate 0,0 corner position to the center of the
	## output image
	if 'output_shape' in kwargs:
		output_shape = kwargs['output_shape']
	else:
		output_shape = ainput.shape
	output_center = output_shape[0]/2.0, output_shape[1]/2.0
	trans3 = Translation(output_center)

	matrix = matrix_chain([trans1, trans2, trans3])
	aoutput = transform(ainput, matrix, **kwargs)
	return aoutput

def test4(point, angle, scale, output_shape):
	import pyami.mrc
	#ainput = pyami.mrc.read('4k-512.mrc')
	ainput = numpy.ones((4096,4096))

	rotation = Rotation(angle)
	scale = Scale(scale)
	mat = matrix_chain((rotation, scale))

	output = transform_centered(ainput, mat, point, output_shape=output_shape)
	pyami.mrc.write(output, 'output.mrc')

def test5(point, angle, scale, output_shape):
	import pyami.mrc
	ainput = pyami.mrc.read('4k.mrc')

	input_center = ainput.shape[0] / 2, ainput.shape[1] / 2
	shift = input_center[0] - point[0], input_center[1] - point[1]

	shifted = scipy.ndimage.shift(ainput, shift)
	rotated = scipy.ndimage.rotate(shifted, angle)
	scaled = scipy.ndimage.zoom(rotated, scale, output_shape=output_shape)

	pyami.mrc.write(output, 'output.mrc')

def test6():
	point = (3184, 1120)  # 4096,4096
	point1 = (3120, 1008)  # 4096,4096
	point2 = (3336, 1336)  # 4096,4096
	vector = point2[0]-point1[0], point2[1]-point1[1]
	angle = numpy.arctan2(vector[1], vector[0])
	scale = 1
	output_shape = (260, 260)

	test4(point, angle, scale, output_shape)

def test7():
	import pyami.mrc
	ainput = pyami.mrc.read('4k.mrc')
	#ainput = numpy.arange(4096*4096)

	mat = Rotation(30*numpy.pi/180.0).matrix
	output = transform_centered(ainput, mat, (0,0), output_shape=(100,100))
	pyami.mrc.write(output, 'output.mrc')

if __name__ == '__main__':
	test7()
