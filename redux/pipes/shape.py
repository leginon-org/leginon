# 3rd party
import math
import numpy

# myami
import pyami.imagefun

# local
from redux.pipe import Pipe
from redux.pipe import shape_converter

#opencv is faster than scipy, but may not be installed
try:
	import cv2
	opencv = True
except ImportError:
	#scipy.misc.imresize changes the image range and fails on FFT
	#import scipy.misc
	opencv = False
import scipy.ndimage.interpolation

def imresize(outputimg, request_shape):
	if opencv is True and len(request_shape) == 2:
		#this is 3x-5x faster than scipy
		height, width = request_shape
		outputimg = cv2.resize(outputimg, (width,height), interpolation=cv2.INTER_LINEAR)
	else:
		#using float64 to avoid rounding errors
		zoomfactors = (
			numpy.array(request_shape, dtype=numpy.float64) /
			numpy.array(outputimg.shape, dtype=numpy.float64) )
		outputimg = scipy.ndimage.interpolation.zoom(outputimg, zoomfactors, order=1, mode='wrap')
	return outputimg

class Shape(Pipe):
	required_args = {'shape': shape_converter}

	@classmethod
	def run(cls, input, shape):
		request_shape = shape

		# that was easy
		if input.shape == request_shape:
			return input

		outputimg = input.copy()

		# make sure shape is same dimensions as input image
		# rgb input image would have one extra dimension
		if len(request_shape) == len(input.shape) == 2:
			#Standard gray scale 2D image
			#get maxbinning in each dimension
			xbin = int(math.floor(input.shape[0]/float(request_shape[0])))
			if xbin < 1: xbin = 1
			ybin = int(math.floor(input.shape[1]/float(request_shape[1])))
			if ybin < 1: ybin = 1
			newshape = (request_shape[0]*xbin, request_shape[1]*ybin)
			outputimg = imresize(outputimg, newshape)
			outputimg = pyami.imagefun.bin(outputimg, xbin, ybin)
		elif len(request_shape) == len(input.shape):
			#Standard gray scale not 2D
			outputimg = imresize(outputimg, request_shape)
		elif len(request_shape) + 1 == len(input.shape) and input.shape[-1] == 3:
			#RGB is Type
			newshape = list(request_shape)
			newshape.append(3)
			outputimg = imresize(outputimg, newshape)
		else:
			#how did we get here?
			raise ValueError('mismatch in number of dimensions: %s -> %s' % (input.shape, request_shape))

		return outputimg

	def make_dirname(self):
		dims = map(str, self.kwargs['shape'])
		dims = 'x'.join(dims)
		self._dirname = dims

if __name__ == "__main__":
	outputshape = (512,512)
	s = Shape(shape=outputshape,is_rgb=True)
	inputshape = (3710,3838)
	import numpy
	a = numpy.ones(inputshape)
	r = s.run(a,outputshape)
	print r.shape
