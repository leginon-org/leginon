#!/usr/bin/env python

import libcv
import math
import time
from pyami import mrc, mem
import numpy
from pyami import quietscipy
from scipy import optimize

#-----------------------
def makeResult(difftilt, bestangle, shift, scale):
	radangle = math.radians(bestangle)
	raddifftilt = math.radians(difftilt)	
	### rotate by radangle, compress by raddifftilt, rotate by -radangle
	if difftilt > 0:
		result = numpy.array([
			[	(math.cos(radangle)**2 + math.sin(radangle)**2*math.cos(raddifftilt))*scale,
				((1.0-math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle))*scale, 
				0.0
			], 
			[	((1.0-math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle))*scale, 
				(math.sin(radangle)**2 + math.cos(radangle)**2*math.cos(raddifftilt))*scale,
				0.0
			], 
			[shift[0], shift[1], 1.0]], 
			dtype=numpy.float32)
	else:
		result = numpy.array([
			[	math.cos(radangle)**2 + math.sin(radangle)**2/math.cos(raddifftilt),
				(1.0-1.0/math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
				0.0
			], 
			[	(1.0-1.0/math.cos(raddifftilt)) * math.cos(radangle)*math.sin(radangle), 
				math.sin(radangle)**2 + math.cos(radangle)**2/math.cos(raddifftilt),
				0.0
			], 
			[shift[0], shift[1], 1.0]], 
			dtype=numpy.float32)
	#print "result=\n", numpy.asarray(result*100, dtype=numpy.int8)
	return result

#-----------------------
def diffResult(x1, c1, c2, c3):
	#print x1
	result = numpy.array([c1,c2,c3], dtype=numpy.float32)
	#print result
	tiltangle = x1[0]
	tiltaxis  = x1[1]
	scale  = x1[2]
	shift = (result[2][0], result[2][1])
	made = makeResult(tiltangle, tiltaxis, shift, scale)
	#print made
	diffmat = (made - result)
	rmsd = (diffmat**2).mean()*100.0
	return rmsd

#-----------------------
def findTilt(result):
	x0 = affineToValues(result)
	solved = optimize.fmin(diffResult, x0, args=((result)), 
		xtol=1e-4, ftol=1e-4, maxiter=500, maxfun=500, disp=0, full_output=1)
	x1 = solved[0]
	tilt = x1[0]
	if tilt > 90:
		tilt -= 180.0
	print "tilt angle=",x1[0]
	print "tilt axis =",x1[1]
	print "scale =",x1[2]
	print "rmsd =",solved[1]
	print "matrix =",makeResult(x1[0], x1[1], (0,0), x1[2])

#-----------------------
def checkLibCVResult(result):
	"""
	Tests whether the libcv resulting affine matrix is reasonable for tilting
	"""
	if result[0][0] < 0.5 or result[1][1] < 0.5:
		#max tilt angle of 60 degrees
		print ("Bad libcv result: bad tilt in matrix: "+affineToText(result))
		print ("Bad libcv result: bad tilt in matrix: "+affineToText(result))
		return False
	elif result[0][0] > 1.1 or result[1][1] > 1.1:
		#only allow 25 degrees of expansion
		print ("Bad libcv result: image expansion: "+affineToText(result))
		print ("Bad libcv result: image expansion: "+affineToText(result))
		return False
	elif abs(result[0][1]) > 0.7071 or abs(result[1][0]) > 0.7071:
		#max rotation angle of 45 degrees
		print ("Bad libcv result: too much rotation: "+affineToText(result))
		print ("Bad libcv result: too much rotation: "+affineToText(result))
		return False
	return True

#-----------------------
def affineToValues(matrix):
	"""
	Converts a libcv matrix into human readable text
	"""
	tiltv = matrix[0,0] * matrix[1,1]
	rotv = (matrix[0,1] - matrix[1,0]) / 2.0
	if abs(tiltv) > 1:
		tilt = math.degrees(math.acos(1.0/tiltv))
	else:
		tilt = math.degrees(math.acos(tiltv))
	if tilt > 90.0:
		tilt = tilt - 180.0
	if abs(rotv) < 1:
		rot = math.degrees(math.asin(rotv))
	else:
		rot = 180.0
	return numpy.array([tilt,rot,1.0], dtype=numpy.float32)

#-----------------------
def affineToText(matrix):
	"""
	Converts a libcv matrix into human readable text
	"""
	tiltv = matrix[0,0] * matrix[1,1]
	rotv = (matrix[0,1] - matrix[1,0]) / 2.0
	if abs(tiltv) > 1:
		tilt = math.degrees(math.acos(1.0/tiltv))
	else:
		tilt = math.degrees(math.acos(tiltv))
	if tilt > 90.0:
		tilt = tilt - 180.0
	if abs(rotv) < 1:
		rot = math.degrees(math.asin(rotv))
	else:
		rot = 180.0
	mystr = ( "tiltang = %.2f, rotation = %.2f, shift = %.2f,%.2f" %
		(tilt, rot, matrix[2,0], matrix[2,1]) )
	return mystr

#-----------------------
def MatchImages(image1, image2, minsize=250, maxsize=0.9, blur=0, sharpen=0, WoB=False, BoW=True):
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
		print "====================="
		result = libcv.MatchImages(image1, image2, minsize, maxsize, blur, sharpen, WoB, BoW)
		print "====================="
		return result
	except:
		return numpy.zeros([3,3], dtype=numpy.float32)

	print ""


if __name__ == "__main__":
	image2 = mrc.read("untilted.mrc")
	image1 = mrc.read("tilted.mrc")
	startmem = mem.active()
	lastmem = startmem
	memlist = []
	for i in range(150):
		result = MatchImages(image1, image2)
		#checkLibCVResult(result)
		#findTilt(result)
		#print numpy.array(result*1000, dtype=numpy.int32)
		memmeg1 = (mem.active()-startmem)/1024.0
		memmeg2 = (mem.active()-lastmem)/1024.0
		lastmem = mem.active()
		print "-->\tMEM: "+str(int(memmeg1))+" MB "
		memlist.append(memmeg2)
		time.sleep(1)
	memarr = numpy.asarray(memlist, dtype=numpy.float32)
	print memarr
	print "Total: ", memarr.mean(), "+/-", memarr.std()


