#!/usr/bin/env python

import numpy
import quietscipy
from scipy import fftpack
import scipy.ndimage
import correlator
import numextension
import mrc
import imagefun
import peakfinder

debug = True

def pad(im, shape):
	im2 = numpy.zeros(shape, im.dtype)
	r0 = shape[0]/2 - im.shape[0]/2
	c0 = shape[1]/2 - im.shape[1]/2
	im2[r0:r0+im.shape[0], c0:c0+im.shape[1]] = im
	return im2

def mrc_write(im, filename):
	if debug:
		mrc.write(im, filename)

def findBestTransformValue(image, reference, start, end, increment, transfunc, *args, **kwargs):
	bestvalue = None
	bestshift = None
	bestsnr = 6.0
	bestnewimage = None
	for i, value in enumerate(numpy.arange(start, end, increment)):
		newimage = transfunc(image, value, *args, **kwargs)
		newimage = pad(newimage, reference.shape)
		cor = correlator.phase_correlate(reference, newimage, zero=False)
		mrc_write(cor, 'cor-%s-%03d.mrc' % (transfunc.__name__, i))
		results = peakfinder.findSubpixelPeak(cor, lpf=1.2)
		shift = correlator.wrap_coord(results['subpixel peak'], cor.shape)
		snr = results['snr']
		if debug:
			print i, value, snr, shift
		if snr > bestsnr:
			bestsnr = snr
			bestvalue = value
			bestshift = shift
			bestnewimage = newimage
	return bestvalue, shift, cor, bestnewimage

def findBestRotation(image, reference, start, end, increment):
	return findBestTransformValue(image, reference, start, end, increment, scipy.ndimage.rotate, reshape=False)

def findBestScale(image, reference, start, end, increment):
	return findBestTransformValue(image, reference, start, end, increment, scipy.ndimage.zoom)

def findShift(image, reference, scale, angle):
	image = scipy.ndimage.zoom(image, scale)
	image = scipy.ndimage.rotate(image, angle)
	image = pad(image, reference.shape)
	cor = correlator.phase_correlate(reference, image, zero=False)
	results = peakfinder.findSubpixelPeak(cor, lpf=1.2)
	shift = correlator.wrap_coord(results['subpixel peak'], cor.shape)

	mrc_write(cor, 'finalcor.mrc')
	mrc_write(image, 'finalimage.mrc')
	mrc_write(reference, 'reference.mrc')

	return shift

def findRotationScale(image, reference, anglestart, angleend, angleinc, scalestart, scaleend, scaleinc):
	## scale image to initial guess
	scaleguess = (float(scalestart) + scaleend) / 2
	print 'SCALEGUESS', scaleguess
	image2 = scipy.ndimage.zoom(image, scaleguess)

	result = findBestRotation(image2, reference, anglestart, angleend, angleinc)
	angle = result[0]
	print 'BEST ANGLE', angle
	image2 = scipy.ndimage.rotate(image, angle)

	result = findBestScale(image2, reference, scalestart, scaleend, scaleinc)
	scale = result[0]
	print 'BEST SCALE', scale

	return angle, scale

def findRotationScaleShift(image, reference, anglestart, angleend, angleinc, scalestart, scaleend, scaleinc, prebin):
	im = imagefun.bin(image, prebin)
	ref = imagefun.bin(reference, prebin)
	angle, scale = findRotationScale(im, ref, anglestart, angleend, angleinc, scalestart, scaleend, scaleinc)
	if None in (angle, scale):
		return None
	shift = findShift(image, reference, scale, angle)
	if shift is None:
		return None
	return angle, scale, shift

def main():
	import mrc
	im1 = mrc.read('/ami/data00/leginon/07sep26cal/rawdata/07sep26cal_00006m.mrc')
	mag1 = 14500
	im2 = mrc.read('/ami/data00/leginon/07sep26cal/rawdata/07sep26cal_00007m.mrc')
	mag2 = 11500
	'''
	im1 = mrc.read('/ami/data00/leginon/07sep26cal/rawdata/07sep26cal_00002m.mrc')
	mag1 = 50000
	im2 = mrc.read('/ami/data00/leginon/07sep26cal/rawdata/07sep26cal_00003m.mrc')
	mag2 = 29000
	'''
	'''
	im1 = mrc.read('/ami/data00/leginon/07sep25jim/rawdata/07sep25jim_00005hl3.mrc')
	mag1 = 7800
	im2 = mrc.read('/ami/data00/leginon/07sep25jim/rawdata/07sep25jim_00005hl2.mrc')
	mag2 = 6500
	'''
	'''
	im1 = mrc.read('/ami/data00/leginon/07sep25jim/rawdata/07sep25jim_00004fa.mrc')
	mag1 = 50000
	im2 = mrc.read('/ami/data00/leginon/07sep25jim/rawdata/07sep25jim_00004fa2.mrc')
	mag2 = 29000
	'''
	'''
	im1 = mrc.read('../images/07apr03a/07apr03a_00003gr_00005sq_v01_00006hl.mrc')
	mag1 = 5000
	im2 = mrc.read('../images/07apr03a/07apr03a_00003gr_00005sq_v01.mrc')
	mag2 = 800
	'''
	#im1 = mrc.read('../images/07sep17jim4/07sep17jim4_00001a.mrc')
	#im2 = mrc.read('../images/07sep17jim4/07sep17jim4_00003a.mrc')
	#im1 = mrc.read('im00.mrc')
	#im2 = mrc.read('im01.mrc')

	scale = float(mag2)/mag1
	scalestart = scale - 0.02
	scaleend = scale + 0.02
	scaleinc = 0.005
	anglestart = -3
	angleend = 3
	angleinc = 0.25
	bin = 4
	binim1 = imagefun.bin(im1, bin)
	binim2 = imagefun.bin(im2, bin)
	rotation, scale = findRotationScale(binim1, binim2, anglestart, angleend, angleinc, scalestart, scaleend, scaleinc)

	shift = findShift(im1, im2, scale, rotation)
	print 'BEST SHIFT', shift

if __name__ == '__main__':
	main()
