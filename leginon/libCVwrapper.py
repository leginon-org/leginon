#!/usr/bin/env python

import threading
import numpy
try:
	import libCV
except:
	pass

def FindRegions(image, minsize=3, maxsize=0.8, blur=0, sharpen=0, WoB=True, BoW=True, depricated=0):
	"""
	Given an image find regions

	Inputs:
		numpy image array
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
		List of Dictionaries with Region Coordinates
		Numpy Image Array
	"""
	try:
		return libCV.FindRegions(image1, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		regions = [
			{'regionEllipse': numpy.zeros([3], dtype=numpy.float32) },
			{'regionEllipse': numpy.ones([3], dtype=numpy.float32) },
		]
		return regions, numpy.zeros([4,4], dtype=numpy.float32)
	#return threading.Thread(target=libCV.FindRegions, args=(image1, image2, minsize, maxsize, blur, sharpen, WoB, BoW)).start()

	print ""

def MatchImages(image1, image2, minsize=0.01, maxsize=0.9, blur=0, sharpen=0, WoB=True, BoW=True):
	"""
	Given two images:
	(1) Find regions
	(2) Match the regions
	(3) Find the affine matrix relating the two images
	
	Inputs:
		numpy image1 array
		numpy image2 array
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
		return libCV.MatchImages(image1, image2, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		return numpy.zeros([3,3], dtype=numpy.float32)
	#return threading.Thread(target=libCV.MatchImages, args=(image1, image2, minsize, maxsize, blur, sharpen, WoB, BoW)).start()

	print ""

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
	#return threading.Thread(target=libCV.PolygonVE, args=(polygon, thresh)).start()
	print ""


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

def checkLibCVResult(self, result):
	"""
	Tests whether the libCV resulting affine matrix is reasonable for tilting
	"""

	if result[0][0] < 0.5 or result[1][1] < 0.5:
		self.logger.error("Bad libCV result: bad matrix")
		return False
	elif result[0][1] > 0.5 or result[1][0] > 0.5:
		self.logger.error('Bad libCV result: too much rotation')
		return False
	return True

def affineToText(matrix):
	"""
	Converts a libCV matrix into human readable text
	"""
	tiltv = matrix[0,0] * matrix[1,1]
	rotv = (matrix[0,1] - matrix[1,0]) / 2.0
	if tiltv > 1:
		tilt = degrees(math.cos(1.0/tiltv))
	else:
		tilt = degrees(math.cos(tiltv))
	rot = degrees(math.asin(rotv))
	return "tiltang = %.2f, rotation = %.2f, shift = %.2f,%.2f"
	

