#!/usr/bin/env python

import pyami.fft
import numpy
import scipy.ndimage
import pyami.affine2

def tilt_image(image, tilt_old, tilt_new, direction, shift=None, **kwargs):
	'''
Transform an image from "tilt_old" to "tilt_new" where the tilt occurs
in the given "direction".  Also shift by "shift".  Angles are in radian.
"direction" is 0 radian in the direction of the 0(row) axis, and goes positive
toward the 1(column) axis.  Additional kwargs may be passed along to the
call to scipy.ndimage.affine_transform.
	'''
	rot_angle = -direction  # may need reverse
	transforms = []
	rot1 = pyami.affine2.Rotation(rot_angle)
	transforms.append(rot1)
	scale = pyami.affine2.Scale(numpy.cos(tilt_new)/numpy.cos(tilt_old), 1.0)
	transforms.append(scale)
	rot2 = pyami.affine2.Rotation(-rot_angle)
	transforms.append(rot2)
	if shift is not None:
		trans = pyami.affine2.Translation(shift)
		transforms.append(trans)
	matrix = pyami.affine2.matrix_chain(transforms)
	center = image.shape[0]/2, image.shape[1]/2
	output = pyami.affine2.transform_centered(image, matrix, center, **kwargs)
	return output

def cross_correlate(im1, im2):
	fft1 = pyami.fft.forward(im1)
	fft2 = pyami.fft.forward(im2)
	ccfft = numpy.multiply(numpy.conjugate(fft1), fft2)
	crosscor = pyami.fft.reverse(ccfft)
	return crosscor

def find_peak(im):
	'''simple peak finder:  find the maximum pixel value'''
	peakindex = numpy.argmax(im)
	peakcoord = numpy.unravel_index(peakindex, im.shape)
	return peakcoord

def dog(im, s1, s2):
	'''difference of gaussians'''
	g1 = scipy.ndimage.gaussian_filter(im, s1, mode='wrap')
	g2 = scipy.ndimage.gaussian_filter(im, s2, mode='wrap')
	d = g1 - g2
	return d

def peakscore(im, coord, label):
	'''
	relative score for a peak to determine if it is real
	'''
	control_coord = coord[0]-im.shape[0]/2, coord[1]-im.shape[1]/2

	roi3 = pyami.imagefun.crop(im, (3,3), coord, mode='wrap')
	roi3_control = pyami.imagefun.crop(im, (3,3), control_coord, mode='wrap')

	roi_mean = roi3.mean()
	control_mean = roi3_control.mean()

	score = abs(roi_mean / control_mean)
	return score

def match_images(old_image, new_image, old_tilt, new_tilt, tilt_direction):
	# transform new image to same tilt as old image
	new_corrected = tilt_image(new_image, new_tilt, old_tilt, tilt_direction, mode='mirror')

	cc = cross_correlate(old_image, new_corrected)
	cc = dog(cc, 0.7, 2.0)
	coord = find_peak(cc)

	# final im2, matched to im1 (tilt and shift)
	shift = coord[0]-old_image.shape[0], coord[1]-old_image.shape[1]
	shift = -shift[0],-shift[1]
	new_corrected = tilt_image(new_image, new_tilt, old_tilt, tilt_direction, shift, mode='constant')

