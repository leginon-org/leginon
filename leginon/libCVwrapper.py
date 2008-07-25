#!/usr/bin/env python

import threading
import numpy
import math
import pyami.quietscipy
from scipy import ndimage
pi = numpy.pi

try:
	import libCV
except:
	pass

#-----------------------
def radians(degrees):
	return float(degrees) * pi / 180.0

#-----------------------
def degrees(radians):
	return float(radians) * 180.0 / pi

#-----------------------
def FindRegions(image, minsize=3, maxsize=0.8, blur=0, sharpen=0, WoB=True, BoW=True, depricated=0):
	"""
	Given an image find regions

	Inputs:
		numpy image array, dtype=float32
		minsize of regions (default: 3 pixels)
			< 1: percentage of image size
			> 1: number of pixels
		maxsize of regions (default: 80% of image)
			< 1: percentage of image size
			> 1: number of pixels
		Blur the image by blur pixels (diabled)
		Sharpen the image by sharpen pixels (diabled)
		Scan for white regions on black background (True/False)
		Scan for black regions on white background (True/False)

	Output:
		Tuple of a List of Dictionaries with 
			'regionBorder' a 2d numpy array with dimension 2 x N and 
			'regionEllipse' a tuple of 11 floats
	"""

	try:
		imfloat = numpy.asarray(image, dtype=numpy.float32)
		return  libCV.FindRegions(imfloat, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		mydict = { 
			'regionBorder': numpy.array([[0,0,0,0]],[[0,0,0,0]]),
			'regionEllipse': (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0),
		}
		mytuple = ( [mydict,], None)
		return numpy.zeros([3,3], dtype=numpy.float32)
	print ""

#-----------------------
def MatchImages(image1, image2, minsize=0.01, maxsize=0.9, blur=0, sharpen=0, WoB=True, BoW=True):
	"""
	Given two images:
	(1) Find regions
	(2) Match the regions
	(3) Find the affine matrix relating the two images
	
	Inputs:
		numpy image1 array, dtype=float32
		numpy image2 array, dtype=float32
		minsize of regions (default: 3 pixels)
			< 1: percentage of image size
			> 1: number of pixels
		maxsize of regions (default: 80% of image)
			< 1: percentage of image size
			> 1: number of pixels
		Blur the image by blur pixels (diabled)
		Sharpen the image by sharpen pixels (diabled)
		Scan for white regions on black background (True/False)
		Scan for black regions on white background (True/False)

	Output:
		3x3 Affine Matrix
	"""

	try:
		imfloat1 = numpy.asarray(image1, dtype=numpy.float32)
		imfloat2 = numpy.asarray(image2, dtype=numpy.float32)
		return libCV.MatchImages(image1, image2, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		return numpy.zeros([3,3], dtype=numpy.float32)

	print ""

#-----------------------
def PolygonVE(polygon, thresh):
	"""

	Inputs:
		numpy list of polygon vertices
		threshold
	"""

	try:
		return libCV.PolygonVE(polygon, thresh)
	except:
		return None
	print ""

#-----------------------
def PolygonACD(array, value):
	"""
	used by libcvcaller.py
	inputs:
		array
		value
	outputs:
		array?
	"""

	try:
		return libCV.PolygonACD(array, value)
	except:
		print "libCV failed in PolygonACD"
		return []


#-----------------------
def checkArrayMinMax(self, a1, a2):
	"""
	Tests whether an image has a valid range for libCV
	"""
	a1b = ndimage.median_filter(a1, size=3)
	min1 = ndimage.minimum(a1b)
	max1 = ndimage.maximum(a1b)
	if max1 - min1 < 10:
		self.logger.error("Old Image Range Error %d" % int(max1 - min1))
		return False
	a2b = ndimage.median_filter(a2, size=3)
	min2 = ndimage.minimum(a2b)
	max2 = ndimage.maximum(a2b)
	if max2 - min2 < 10:
		self.logger.error("New Image Range Error %d" % int(max2 - min2))
		return False
	return True

#-----------------------
def checkLibCVResult(self, result):
	"""
	Tests whether the libCV resulting affine matrix is reasonable for tilting
	"""
	if result[0][0] < 0.5 or result[1][1] < 0.5:
		#max tilt angle of 60 degrees
		self.logger.warning("Bad libCV result: bad tilt in matrix: "+affineToText(result))
		return False
	elif result[0][0] > 1.1 or result[1][1] > 1.1:
		#only allow 25 degrees of expansion
		self.logger.warning("Bad libCV result: image expansion: "+affineToText(result))
		return False
	elif abs(result[0][1]) > 0.4 or abs(result[1][0]) > 0.4:
		#max rotation angle of 25 degrees
		self.logger.warning("Bad libCV result: too much rotation: "+affineToText(result))
		return False
	return True

#-----------------------
def affineToText(matrix):
	"""
	Converts a libCV matrix into human readable text
	"""
	tiltv = matrix[0,0] * matrix[1,1]
	rotv = (matrix[0,1] - matrix[1,0]) / 2.0
	if tiltv > 1:
		tilt = degrees(math.acos(1.0/tiltv))
	else:
		tilt = degrees(math.acos(tiltv))
	if rotv < 1:
		rot = degrees(math.asin(rotv))
	else:
		rot = 180.0
	mystr = ( "tiltang = %.2f, rotation = %.2f, shift = %.2f,%.2f" %
		(tilt, rot, matrix[2,0], matrix[2,1]) )
	return mystr
	

