#!/usr/bin/env python

import threading
import numpy
import math
import pyami.quietscipy
from scipy import ndimage
from numpy import linalg
pi = numpy.pi

try:
	import libcv
	#print "libcv found"
except:
	#print "libcv not found"
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
		scaled = scaleAndPlane(image)
		return libcv.FindRegions(scaled, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		print "libcv.FindRegions failed"
		mydict = { 
			'regionBorder': numpy.array([[0,0,0,0],[0,0,0,0]]),
			'regionEllipse': (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0),
		}
		mytuple = ( [mydict,], None)
		return mytuple

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
		scaled1 = scaleAndPlane(image1)
		scaled2 = scaleAndPlane(image2)
		return libcv.MatchImages(scaled1, scaled2, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		print "libcv.MatchImages failed"
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
		return libcv.PolygonVE(polygon, thresh)
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
		return libcv.PolygonACD(array, value)
	except:
		print "libcv failed in PolygonACD"
		return []


#-----------------------
def checkArrayMinMax(self, a1, a2):
	"""
	Tests whether an image has a valid range for libcv
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
	Tests whether the libcv resulting affine matrix is reasonable for tilting
	"""
	if abs(result[0][0]) < 0.5 or abs(result[1][1]) < 0.5:
		#max tilt angle of 60 degrees
		self.logger.warning("Bad libcv result: bad tilt in matrix: "+affineToText(result))
		print ("Bad libcv result: bad tilt in matrix: "+affineToText(result))
		return False
	elif abs(result[0][0]) > 1.5 or abs(result[1][1]) > 1.5:
		#only allow 25 degrees of expansion
		self.logger.warning("Bad libcv result: image expansion: "+affineToText(result))
		print ("Bad libcv result: image expansion: "+affineToText(result))
		return False
	elif abs(result[0][1]) > 0.7071 or abs(result[1][0]) > 0.7071:
		#max rotation angle of 45 degrees
		self.logger.warning("Bad libcv result: too much rotation: "+affineToText(result))
		print ("Bad libcv result: too much rotation: "+affineToText(result))
		return False
	#elif abs(result[2][0]) > 200 or abs(result[2][1]) > 200:
	#	#max rotation angle of 45 degrees
	#	self.logger.warning("Bad libcv result: too much shift: "+affineToText(result))
	#	print ("Bad libcv result: too much shift: "+affineToText(result))
	#	return False
	return True

#-----------------------
def affineToText(matrix):
	"""
	Converts a libcv matrix into human readable text
	"""
	tiltv = matrix[0,0] * matrix[1,1]
	rotv = (matrix[0,1] - matrix[1,0]) / 2.0
	if abs(tiltv) > 1:
		tilt = degrees(math.acos(1.0/tiltv))
	else:
		tilt = degrees(math.acos(tiltv))
	if tilt > 90.0:
		tilt = tilt - 180.0
	if abs(rotv) < 1:
		rot = degrees(math.asin(rotv))
	else:
		rot = 180.0
	mystr = ( "tiltang = %.2f, rotation = %.2f, shift = %.2f,%.2f" %
		(tilt, rot, matrix[2,0], matrix[2,1]) )
	return mystr


#-----------------------
def scaleAndPlane(imgarray):
	try:
		planed = planeRegression(imgarray)
	except:
		print "regression failed"
		planed = imgarray
	### libcv assumes all types are float32
	try:
		floating = numpy.asarray(planed - planed.min(), dtype=numpy.float32)*1.0e2
	except:
		print "float-ing failed"
		floating = planed
	return floating

#-----------------------
def planeRegression(imgarray):
	"""
	performs a two-dimensional linear regression and subtracts it from an image
	essentially a fast high pass filter
	"""
	size = (imgarray.shape)[0]
	count = float((imgarray.shape)[0]*(imgarray.shape)[1])
	def retx(y,x):
		return x
	def rety(y,x):
		return y
	xarray = numpy.fromfunction(retx, imgarray.shape)
	yarray = numpy.fromfunction(rety, imgarray.shape)
	xsum = float(xarray.sum())
	xsumsq = float((xarray*xarray).sum())
	ysum = xsum
	ysumsq = xsumsq
	xysum = float((xarray*yarray).sum())
	xzsum = float((xarray*imgarray).sum())
	yzsum = float((yarray*imgarray).sum())
	zsum = imgarray.sum()
	zsumsq = (imgarray*imgarray).sum()
	xarray = xarray.astype(numpy.float32)
	yarray = yarray.astype(numpy.float32)
	leftmat = numpy.array( [[xsumsq, xysum, xsum], [xysum, ysumsq, ysum], [xsum, ysum, count]] )
	rightmat = numpy.array( [xzsum, yzsum, zsum] )
	resvec = linalg.solve(leftmat,rightmat)
	#print " ... plane_regress: x-slope:",round(resvec[0]*size,5),\
	#	", y-slope:",round(resvec[1]*size,5),", xy-intercept:",round(resvec[2],5)
	newarray = imgarray - xarray*resvec[0] - yarray*resvec[1] - resvec[2]
	#del imgarray,xarray,yarray,resvec
	return newarray
