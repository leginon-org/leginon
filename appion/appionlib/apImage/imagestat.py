#Part of the new pyappion

## pythonlib
import os
import math
## numpy
import pyami.quietscipy
from numpy import ma
## appion
from appionlib import apDisplay
from appionlib.apImage import imagenorm

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#=========================
def meanEdgeValue(imgdata, w=0):
	"""
	get the average values for the edges of width = w pixels
	"""
	xmax = imgdata.shape[0]
	ymax = imgdata.shape[1]
	leftEdgeAvg   = (imgdata[0:xmax,      0:w]).mean()
	rightEdgeAvg  = (imgdata[0:xmax,      ymax-w:ymax]).mean()
	topEdgeAvg    = (imgdata[0:w,         0:ymax]).mean()
	bottomEdgeAvg = (imgdata[xmax-w:xmax, 0:ymax]).mean()
	edgeAvg       = (leftEdgeAvg + rightEdgeAvg + topEdgeAvg + bottomEdgeAvg)/4.0
	return edgeAvg

#=========================
def centralMean(imgarray, trim=0.1):
	"""
	get the average values for the edges of trim = x percent
	"""
	a = imagenorm.cutEdges(imgarray,trim=trim)
	return a.mean()

#=========================
def maskImageStats(mimage):
	n=ma.count(mimage)
	mimagesq=mimage*mimage
	sum1=ma.sum(mimage)
	sum2=ma.sum(sum1)
	sumsq1=ma.sum(mimagesq)
	sumsq2=ma.sum(sumsq1)
	avg=sum2/n
	if (n > 1):
		stdev=math.sqrt((sumsq2-sum2*sum2/n)/(n-1))
	else:
		stdev=2e20
	return n,avg,stdev

#=========================
def getImageInfo(im):
	"""
	prints out image information good for debugging
	"""
	avg1 = im.mean()
	stdev1 = im.std()
	min1 = im.min()
	max1 = im.max()

	return avg1,stdev1,min1,max1

#=========================
def printImageInfo(im):
	"""
	prints out image information good for debugging
	"""
	#print " ... size: ",im.shape
	#print " ... sum:  ",im.sum()
	avg1,stdev1,min1,max1 = getImageInfo(im)

	print " ... avg:  ",round(avg1,6),"+-",round(stdev1,6)
	print " ... range:",round(min1,6),"<>",round(max1,6)

	return avg1,stdev1,min1,max1

#=========================
def correlationCoefficient(x,y,mask=None):
	"""
	calcualate the correlation coefficient of two numpys
	"""
	if x.shape != y.shape:
		apDisplay.printError("images are not the same shape in correlation calc")
	if mask != None:
		if x.shape != mask.shape:
			apDisplay.printError("mask is not the same shape as images in correlation calc")
		tot = mask.sum()
		if tot == 0:
			return 0.0
		x = imagenorm.normStdevMask(x,mask)
		y = imagenorm.normStdevMask(y,mask)
	else:
		tot = float(x.shape[0]*x.shape[1])
		x = imagenorm.normStdev(x)
		y = imagenorm.normStdev(y)
	z = x*y
	if mask != None:
		z = z*mask
	sm  = z.sum()
	return sm/tot

#=========================
def rmsd(x,y,mask=None):
	return math.sqrt(msd(x,y,mask=mask))

#=========================
def msd(x,y,mask=None):
	if mask != None:
		tot = float(mask.sum())
		if tot == 0:
			return 1.0e13
		x = imagenorm.normStdevMask(x,mask)
		y = imagenorm.normStdevMask(y,mask)
	else:
		tot = float(x.shape[0]*x.shape[1])
		x = imagenorm.normStdev(x)
		y = imagenorm.normStdev(y)
	z = (x-y)**2
	if mask != None:
		z = z*mask
	sm  = z.sum()
	return sm/tot

####
# This is a low-level file with NO database connections
# Please keep it this way
####
