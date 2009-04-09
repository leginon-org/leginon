#!/usr/bin/env python

import numpy
import math
from pyami import quietscipy
from scipy import fftpack
from pyami import mrc, imagefun

#===========
def real_fft2d(*args, **kwargs):
	return fftpack.fft2(*args, **kwargs)

#===========
def inverse_real_fft2d(*args, **kwargs):
	return fftpack.ifft2(*args, **kwargs).real

#===========
def polarToCart(rad, thrad):
	#thrad = thdeg*math.pi/180.0
	x = rad*math.cos(thrad)
	y = rad*math.sin(thrad)
	return x,y

#===========
def cartToPolar(x, y):
	r = math.hypot(x,y)
	if x > 0:
		if y < 0:
			th = math.atan2(y,x)
		else:
			th = math.atan2(y,x) + 2*math.pi
	elif x < 0:
		th = math.atan2(y,x) + math.pi
	else:
		#x = 0
		if y > 0:
			th = 3*math.pi/2.0
		elif y < 0:
			th = math.pi/2.0
		else:
			#x,y = 0
			th = 0
	return r, th*180.0/math.pi

#===========
def linearizeFourierShell(fftim):
	fftshape = numpy.asarray(fftim.shape, dtype=numpy.float32)
	fftcenter = fftshape/2.0
	print fftshape
	print fftcenter
	length = int(math.ceil(max(fftshape)/math.sqrt(2.0)/2.0))
	print length
	linear = numpy.zeros((length), dtype=numpy.uint8)

	for i in range(fftshape[0]):
		for j in range(fftshape[1]):
			x = float(i - fftcenter[0])
			y = float(j - fftcenter[1])
			r, a = cartToPolar(x, y)
			linear[int(r*0.5)] += 1
	print linear 

#===========
def printImageInfo(image):
	print "+++++++++++++"
	print image.shape
	print image.dtype
	print image.mean(), image.std()
	print image.min(), image.max()
	print "============="

#===========
if __name__ == "__main__":
	a = mrc.read("/home/vossman/leginon/holetemplate.mrc")
	a = imagefun.bin2(a, 1)
	printImageInfo(a)
	b = real_fft2d(a)
	printImageInfo(b)
	linearizeFourierShell(b)


#######################################
# Taken from:
#  https://svn.origo.ethz.ch/sas-rigid/src/
#######################################

def rotational_average(field,  segment=360.0,  increment=0.5):
	"""
	calculates the rotational average
	invoke like:
	   rotational_average(<input>, [segment=angle], [increment=angle]
	parameters:
	   input - an input array or Image instance
	   segment - the angular segment in degrees
	   increment - the angular increment in degrees
	returns a ndarray
	"""
	# we can actually only work with Image instances, here
	# therefore do a check
	if isinstance(field,  numpy.ndarray):
		image = toimage(field)
    
	rotated = list()
	for angle in numpy.linspace(0,  segment,  segment/increment):
		rotated.append(image.rotate(angle))
	# convert (back) to numpy arrays
	rotated = [numpy.array(rot) for rot in rotated]
	# add all together
	total = rotated[0]
	for rot in rotated[1:]:
		total += rot
	total = normalize(total)
	return total

def correlation_coefficient(array1,  array2,  mask=None):
	"""
	returns the correlation coefficient of two 2D arrays
        
	invoke like:
		correlation_coefficient(array1,  array2,  [mask])
	input parameters:
		array1, array2: the two input arrays
		mask (optional): a 2D mask, only where the mask contains a value
			the ccc is calculated
	"""
	# in case lists got transferred
	array1 = numpy.asarray(array1)
	array2 = numpy.asarray(array2)
	# as a first step, normalize all arrays to be between 0 and 1
	array1 = normalize(array1)
	array2 = normalize(array2)
	if mask:
		mask2 = normalize(mask.content)
	# correlate arrays:
	corr = correlate2d(array1,  array2)
	if mask:
		ccc = sum(numpy.where(mask,  corr,  0).flatten()) / len(mask2.ravel().trim_zeros())
	else:
		ccc = sum(corr.flatten()) / (array1.shape[0] * array1.shape[1])
	return ccc

