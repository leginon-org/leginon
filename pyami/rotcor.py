#!/usr/bin/env python

import sys
from pyami import mrc
from pyami import correlator
from pyami import peakfinder
from pyami import imagefun
import scipy.fftpack
import scipy.ndimage
import scipy
import numpy

def makeMapping(output_shape, center, dr, dt):
	key = (output_shape, center, dr, dt)
	if key in mappings:
		return mappings[key]
	output_rows, output_cols = numpy.indices(output_shape)
	output_rs = dr * output_rows
	output_ts = dt * output_cols
	rows = output_rs * numpy.cos(output_ts)
	cols = output_rs * numpy.sin(output_ts)
	input_rows = center[0] + rows
	input_cols = center[1] + cols
	mappingshape = output_shape + (2,)
	mapping = numpy.zeros(mappingshape)
	mapping[:,:,0] = input_rows
	mapping[:,:,1] = input_cols
	mappings[key] = mapping
	return mapping
mappings = {}

def dummy(output, mappingarray):
	return tuple(mappingarray.__getitem__(output))

def polar_transform(image, output_shape, center):
	n = min(image.shape)
	dr = n / numpy.sqrt(2) / output_shape[0]
	dt = numpy.pi / output_shape[1]
	print 'AAA'
	mapping = makeMapping(output_shape, center, dr, dt)
	print 'BBB'
	return scipy.ndimage.geometric_transform(image, dummy, output_shape=output_shape, mode='constant', cval=0, extra_arguments=(mapping,), order=1)
	#return scipy.ndimage.geometric_transform(image, mapping.__getitem__, output_shape=output_shape, mode='constant', cval=0)

# correlate polar transform of fft magnitude (shift independent) to find
# best rotation, then rotate to same angle and do normal correlation
def register(image1, image2):
	trim = 8
	image1 = image1[trim:-trim, trim:-trim]
	image2 = image2[trim:-trim, trim:-trim]
	fft1 = scipy.fftpack.fft2(image1)
	fft2 = scipy.fftpack.fft2(image2)

	fft1 = scipy.fftpack.fftshift(fft1, axes=[0])
	fft2 = scipy.fftpack.fftshift(fft2, axes=[0])

	c = int(fft1.shape[0] / 2.0)
	fft1 = fft1[:,:c+1]
	fft2 = fft2[:,:c+1]

	mag1 = numpy.abs(fft1)
	mag2 = numpy.abs(fft2)
	mrc.write(mag1, 'mag1.mrc')
	mrc.write(mag2, 'mag2.mrc')

	center = c,0
	output_shape = c,c
	print 'P1'
	p1 = polar_transform(mag1, output_shape, center)
	#scipy.misc.imsave('p1.jpg', p1)
	mrc.write(p1, 'p1.mrc')
	print 'P2'
	p2 = polar_transform(mag2, output_shape, center)
	#scipy.misc.imsave('p2.jpg', p2)
	mrc.write(p2, 'p2.mrc')

	pc = correlator.phase_correlate(p1, p2, zero=False)
	#pc = correlator.cross_correlate(p1, p2)
	mrc.write(pc, 'pc.mrc')

	#return p1, p2

## just rotate image2 to different angles and correlate
def register2(image1, image2, angles):
	im2filt = scipy.ndimage.spline_filter(image2)
	peaks = []
	for angle in angles:
		image2 = scipy.ndimage.rotate(im2filt, angle, reshape=False)
		#mrc.write(image2, 'rot.mrc')
		pc = correlator.phase_correlate(image1, image2, zero=False)
		mrc.write(pc, 'pc.mrc')
		peak = peakfinder.findSubpixelPeak(pc)
		result = (angle, peak['pixel peak value'], peak['subpixel peak value'], peak['snr'])
		print result
		peaks.append(result)
	return peaks

def testMRCImages():
	file1,file2 = sys.argv[1:3]
	print 'reading MRCs'
	image1 = mrc.read(file1)
	image2 = mrc.read(file2)
	image1 = imagefun.bin(image1, 4)
	image2 = imagefun.bin(image2, 4)
	print 'register...'
	#result = register(image1, image2, range()
	#result = register2(image1, image2, range(86,95))
	result = register2(image1, image2, range(90,91))
	#print result

def testPolarOnImage():
	infilename = sys.argv[1]
	outfilename = sys.argv[2]
	im = scipy.misc.imread(infilename, flatten=True)
	center = im.shape[0]/2.0, im.shape[1]/2.0
	pol = polar_transform(im, (128,128), center)
	scipy.misc.imsave(outfilename, pol)

def testRandomImages(size):
	import numpy.random
	image1 = numpy.random.normal(100, 10, (size,size))
	image2 = numpy.random.normal(100, 10, (size,size))
	result = register(image1, image2)
	print result

if __name__ == '__main__':
	#testRandomImages(8)
	testMRCImages()
	#testPolarOnImage()
