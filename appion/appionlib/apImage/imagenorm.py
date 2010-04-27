#Part of the new pyappion

## pythonlib
import os
import math
## numpy
import numpy
import pyami.quietscipy
from scipy import ndimage
## appion
from appionlib import apDisplay

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#=========================
def normRange(imgarray):
	"""
	normalize the range of an image between 0 and 1
	"""
	min1=imgarray.min()
	max1=imgarray.max()
	if min1 == max1:
		return imgarray - min1
	return (imgarray - min1)/(max1 - min1)

#=========================
def normRangeMed(imgarray, size=5):
	"""
	normalize an image to mean = 0 and stddev = 1.0
	"""
	medimgarray = ndimage.median_filter(imgarray, size=size)
	min1 = medimgarray.min()
	max1 = medimgarray.max()
	if min1 == max1:
		return imgarray - min1
	return (imgarray - min1)/(max1 - min1)

#=========================
def normStdev(imgarray):
	"""
	normalize an image to mean = 0 and stddev = 1.0
	"""
	avg1=imgarray.mean()
	std1=imgarray.std()
	if std1 == 0:
		return imgarray - avg1
	return (imgarray - avg1)/std1

#=========================
def normStdevMed(imgarray, size=3):
	"""
	normalize an image to mean = 0 and stddev = 1.0
	"""
	medimgarray = ndimage.median_filter(imgarray, size=size)
	avg1=medimgarray.mean()
	std1=medimgarray.std()
	if std1 == 0:
		return imgarray - avg1
	return (imgarray - avg1)/std1

#=========================
def normStdevMask(img,mask):
	"""
	normalize an image with mean = 0 and stddev = 1.0 only inside a mask
	"""
	n1	 = mask.sum()
	if n1 == 0:
		return img
	sum1   = (img*mask).sum()
	sumsq1 = (img*img*mask).sum()
	avg1   = sum1/n1
	std1   = math.sqrt((sumsq1 - sum1*sum1/n1)/(n1-1))
	std2   = img.std()
	return (img - avg1) / std1

#=========================
def _maxNormalizeImage(a, stdevLimit=3.0):
	"""
	Normalizes numpy to fit into an image format,
	but maximizes the contrast
	"""
	return _normalizeImage(a, stdevLimit, minlevel= 20.0, maxlevel=240.0, trim=0.1)

#=========================
def _blackNormalizeImage(a, stdevLimit=3.0):
	"""
	Normalizes numpy to fit into an image format,
	but makes it a darker than normal
	"""
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel= 0.0,maxlevel=200.0)

#=========================
def _whiteNormalizeImage(a, stdevLimit=3.0):
	"""
	Normalizes numpy to fit into an image format,
	but makes it a lighter than normal
	"""
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel=55.0,maxlevel=255.0,trim=0.0)

#=========================
def _normalizeImage(img, stdevLimit=3.0, minlevel=0.0, maxlevel=255.0, trim=0.0):
	"""
	Normalizes numpy to fit into an image format
	that is values between 0 (minlevel) and 255 (maxlevel).
	"""
	mid = cutEdges(img,trim)

	imrange = maxlevel - minlevel

	#GET IMAGE STATS
	
	avg1 = im.mean()
	stdev1 = im.std()
	min1 = im.min()
	max1 = im.max()
	#print avg1, stdev1, min1, max1

	#IF MIN/MAX are too high set them to smaller values
	if (min1 < avg1-stdevLimit*stdev1):
		min1 = avg1-stdevLimit*stdev1
	if (max1 > avg1+stdevLimit*stdev1):
		max1 = avg1+stdevLimit*stdev1

	if min1 == max1:
		#case of image == constant
		return img - min1

	if abs(min1) < 0.01 and abs(max1 - 1.0) < 0.01:
		#we have a mask-like object
		return img * 255
	#print min1, max1


	img = (img - min1)/(max1 - min1)*imrange + minlevel
	img = numpy.where(img > maxlevel, 255.0, img)
	img = numpy.where(img < minlevel,   0.0, img)

	return img

#=========================
def cutEdges(img, trim=0.1):
	"""
	cut the edges of an image off by trim percent
	0.0 < trim < 1.0
	"""
	if trim >= 100.0 or trim < 0.0:
		apDisplay.printError("trim ("+str(trim)+") is out of range in cutEdges")
	elif trim >= 1.0:
		trim = trim/100.0
	elif trim == 0:
		return img
	sidetrim = trim/2.0
	xcut1 = int(img.shape[0]*sidetrim)
	ycut1 = int(img.shape[1]*sidetrim)
	xcut2 = int(img.shape[0]*(1.0-sidetrim))
	ycut2 = int(img.shape[1]*(1.0-sidetrim))
	mid = img[xcut1:xcut2,ycut1:ycut2].copy()

	return mid

####
# This is a low-level file with NO database connections
# Please keep it this way
####
