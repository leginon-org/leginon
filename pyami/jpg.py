#!/usr/bin/env python

from PIL import Image
import numpy
import arraystats

def write(a, filename, min=None, max=None, quality=80, newsize=None, stdval=5):
	'''
Write a 2-D numpy array to a JPEG file.
Usage:
	write(array, filename)

Optional arguments 'min' and 'max' will determine what range of the
input array will be scaled to 0-255 in the jpg file.  The default
is to use the following calculation:
   min = mean - 3 * stdev
   max = mean + 3 * stdev

Optional argument 'quality' is used for jpeg quality, a number between
1 and 100.   The default is 80.

Optional argument 'newsize' is used for scaling the image.
	'''
	
	## auto determination of range for scaling to 8 bit.
	if min is None:
		mean = arraystats.mean(a)
		std = arraystats.std(a)
		min = mean - stdval * std
	if max is None:
		mean = arraystats.mean(a)
		std = arraystats.std(a)
		max = mean + stdval * std

	## scale to 8 bit
	a = numpy.clip(a, min, max)
	scale = 255.0 / (max - min)
	a = scale * (a - min)
	a = a.astype(numpy.uint8)

	## use PIL to write JPEG
	imsize = a.shape[1], a.shape[0]
	nstr = a.tostring()
	image = Image.fromstring('L', imsize, nstr, 'raw', 'L', 0, 1)
	image.convert('L').save(filename, "JPEG", quality=quality)
	if newsize is None:
		image.convert('L').save(filename, "JPEG", quality=quality)
	else:
		image.convert('L').resize(newsize).save(filename, "JPEG", quality=quality)

def test():
	size = 256
	a = numpy.arange(size*size)
	a.shape = size,size
	write(a, 'range.jpg')

if __name__ == '__main__':
	test()
