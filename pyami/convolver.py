#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import numpy
import fftengine

class Convolver(object):
	'''
	Provides an efficent convolution calculator.

	Create an instance with two optional arguments:
	     'kernel':  a convolution kernel as a 2-d numpy array
	     'image':  the subject image as a 2-d numpy array
	These values can also be set later using the setKernel and 
	setImage methods.  The convolution is executed using the method
	'convolve', which takes the same two optional arguments.

	A convolver object is efficient at doing a series of convolutions
	for a couple reasons:

	- Individually convolving one kernel on multiple images:
	When a new kernel is set, the convolver maintains a dictionary
	of kernel image FFTs indexed by image shape.  If you want to use
	the same kernel on a series of images, it only needs to compute
	the kernel FFT once for every image shape it receives.

	- Convolving a series of kernels on a single image:
	When a convolution is performed, the FFT of the result is saved.
	You can execute another convolution on this image using the same or
	different kernel.  The FFT of the image does not have to be recomputed.
	'''
	def __init__(self, kernel=None, image=None):
		self.fftengine = fftengine.fftEngine()

		self.kernel = None
		self.shape = None
		self.image_fft = None
		self.kernel_fft = {}

		if kernel is not None:
			self.setKernel(kernel)
		if image is not None:
			self.setImage(image)
		
	def setKernel(self, kernel):
		self.kernel = numpy.asarray(kernel, numpy.float32)
		self.kernel_fft = {}

	def setImage(self, image):
		self.shape = image.shape
		self.image_fft = self.fftengine.transform(image)
		self.makeKernelFFT()

	def makeKernelFFT(self):
		if self.kernel is None:
			return None
		if self.shape in self.kernel_fft:
			return self.kernel_fft[self.shape]

		kim = numpy.zeros(self.shape, numpy.float32)
		### center the kernel at 0,0 in the image
		k = self.kernel
		kind = numpy.indices(k.shape)
		krows = kind[0]
		kcols = kind[1]
		kr,kc = self.kernel.shape
		kr2 = int(kr/2)
		kc2 = int(kc/2)
		imrows = krows - kr2
		imcols = kcols - kc2
		for i in range(kr*kc):
			ir = imrows.flat[i]
			ic = imcols.flat[i]
			kr = krows.flat[i]
			kc = kcols.flat[i]
			kim[ir,ic] = k[kr,kc]
		kfft = self.fftengine.transform(kim)
		self.kernel_fft[self.shape] = kfft
		return kfft

	def convolve(self, image=None, kernel=None, last_image=False, border=None):
		if image is not None and last_image:
			raise ValueError('cannot use both a new image and the last image')
		imfft = self.image_fft
		if image is not None:
			self.setImage(image)
			imfft = self.image_fft
		if kernel is not None:
			self.setKernel(kernel)
		if last_image:
			imfft = self.result_fft

		kfft = self.makeKernelFFT()
		self.result_fft = numpy.multiply(kfft, imfft)
		result = self.fftengine.itransform(self.result_fft)

		# what to do with border?
		n = len(self.kernel)
		if border == 'zero':
			result[:n] = 0
			result[:,:n] = 0
			result[:,-n:] = 0
			result[-n:] = 0

		return result


########
######## common convolution kernels
########

#### 3x3 Laplacian
laplacian_kernel3 = numpy.array((0,-1,0,-1,4,-1,0,-1,0), numpy.float32)
laplacian_kernel3.shape = (3,3)

#### 5x5 Laplacian
laplacian_kernel5 = -numpy.ones((5,5), numpy.float32)
laplacian_kernel5[2,2] = 24.0

#### Gaussian
def gaussian_kernel(sigma):
	'''
	produces gaussian smoothing kernel
	'''
	if sigma < 0.1:
		## sigma is very small and probably shouldn't be doing this at all
		## so just make delta function
		return numpy.ones((1,1), numpy.float32)
	half = int(5 * sigma)
	n = 2 * half + 1
	k1 = 1.0 / (2.0 * numpy.pi * sigma**2)
	def i(rows,cols):
		rows = numpy.asarray(rows, numpy.float32)
		cols = numpy.asarray(cols, numpy.float32)
		rows = rows - half
		cols = cols - half
		k2 = numpy.exp(-(rows**2+cols**2) / 2.0 / sigma**2)
		return k1 * k2
	k = numpy.fromfunction(i, (n,n))
	k = numpy.asarray(k, numpy.float32)
	return k

#### Laplacian of Gaussian
def laplacian_of_gaussian_kernel(n, sigma):
	if not n % 2:
		raise ValueError('kernel size must be odd')
	half = (n - 1) / 2
	def func(x,y):
		f1 = (x**2 + y**2) / 2.0 / sigma**2
		f2 = -1.0 / numpy.pi / (sigma**4)
		f3 = 1 - f1
		f4 = numpy.exp(-f1)
		return f2 * f3 * f4
	k = numpy.zeros((n,n), numpy.float32)
	for row in range(n):
		x = row - half
		for col in range(n):
			y = col - half
			k[row,col] = func(x,y)
	return k

#### Sobel Row Derivative
sobel_row_kernel = numpy.array((1,2,1,0,0,0,-1,-2,-1), numpy.float32)
sobel_row_kernel.shape = (3,3)

#### Sobel Column Derivative
sobel_col_kernel = numpy.array((1,0,-1,2,0,-2,1,0,-1), numpy.float32)
sobel_col_kernel.shape = (3,3)


if __name__ == '__main__':
	import Mrc
	import sys
	import imagefun

	filename = sys.argv[1]

	sobel_row = numpy.array((1,2,1,0,0,0,-1,-2,-1), numpy.float32)
	sobel_row.shape = (3,3)
	sobel_col = numpy.array((1,0,-1,2,0,-2,1,0,-1), numpy.float32)
	sobel_col.shape = (3,3)
	gauss = imagefun.gaussian_kernel(1.6)

	c = Convolver()

	im = Mrc.mrc_to_numeric(filename)

	c.setImage(image=im)
	s = c.convolve(kernel=gauss)
	r = c.convolve(kernel=sobel_row, image=s)
	c = c.convolve(kernel=sobel_col, image=s)
	edge = numpy.sqrt(r**2 + c**2)
	Mrc.numeric_to_mrc(edge, 'edge.mrc')
