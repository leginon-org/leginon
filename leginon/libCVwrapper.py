#!/usr/bin/env python

import threading
import numpy
try:
	import libCV
except:
	pass

def FindRegions(image, minsize=0.01, maxsize=0.9, blur=0, sharpen=0, WoB=True, BoW=True):
	"""
	Given an image find regions

	Inputs:
		numpy image array
		minsize of regions
			< 1: percentage of image size
			> 1: number of pixels
		maxsize of regions
			< 1: percentage of image size
			> 1: number of pixels
		Blur the image by blur pixels (diabled)
		Sharpen the image by sharpen pixels (diabled)
		Scan for white regions on black background (T/F)
		Scan for black regions on white background (T/F)
	"""
	try:
		return libCV.FindRegions(image1, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		return numpy.array([[0,0],[0,0]], dtype=numpy.float32)
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
		minsize of regions
			< 1: percentage of image size
			> 1: number of pixels
		maxsize of regions
			< 1: percentage of image size
			> 1: number of pixels
		Blur the image by blur pixels (diabled)
		Sharpen the image by sharpen pixels (diabled)
		Scan for white regions on black background (T/F)
		Scan for black regions on white background (T/F)		
	"""
	try:
		return libCV.MatchImages(image1, image2, minsize, maxsize, blur, sharpen, WoB, BoW)
	except:
		return numpy.array([0,0,0],[0,0,0],[0,0,0], dtype=numpy.float32)
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

if __name__ == "__main__":

