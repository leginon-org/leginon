#!/usr/bin/env python

import copy
import time
import math
import numpy
#from matplotlib import pyplot
import scipy.ndimage.measurements
from pyami import ellipse
from appionlib.apCtf import ctftools
from appionlib.apImage import imagefilter


debug = False

#=========================================
def showImage(image):
	if debug is False:
		return
	pyplot.clf()
	pyplot.imshow(image)
	pyplot.gray()
	pyplot.show()
	time.sleep(0.1)
	return

#=========================================
def findAstigmatism(fftarray, freq, defocus, resolution, ctfvalues, peakNum=1):
	"""
	find the astigmatism from a radial 1D estimate of the defocus
	"""
	#searchError = resolution/100.

	extrema = ctftools.getCtfExtrema(defocus, freq*1e10,
		ctfvalues['cs'], ctfvalues['volts'], ctfvalues['amplitude_contrast'],
		numzeros=peakNum*2+1, zerotype="all")
	if len(extrema) < 2*peakNum:
		return None
	minEdgeRadius = int(math.ceil(extrema[peakNum-1])) #first peak
	maxEdgeRadius = int(math.ceil(extrema[peakNum])) #second peak
	newshape = (maxEdgeRadius*2, maxEdgeRadius*2)

	print "newshape",newshape

	fftcenter = copy.deepcopy(imagefilter.frame_cut(fftarray, newshape))
	showImage(fftcenter)

	shape = fftcenter.shape
	## create a grid of distance from the center
	xhalfshape = shape[0]/2.0
	x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
	yhalfshape = shape[1]/2.0
	y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
	xx, yy = numpy.meshgrid(x, y)
	radialArray = xx**2 + yy**2 - 0.5
	#radialArray = numpy.sqrt(radial)

	maxVal = fftcenter.max()*2
	minVal = fftcenter.min()
	if debug is True:
		fftcenter = numpy.where(radialArray > maxEdgeRadius**2, maxVal, fftcenter)
		showImage(fftcenter)
		fftcenter = numpy.where(radialArray < minEdgeRadius**2, maxVal, fftcenter)
		showImage(fftcenter)

	angleArray = numpy.arctan2(-yy,xx)
	numSteps = 360
	angleArray += math.pi
	angleArray /= 2*math.pi
	angleArray *= numSteps
	angleArray = numpy.asarray(angleArray, dtype=numpy.uint16)

	showImage(angleArray)

	dataIntegers = numpy.array(range(numSteps))

	xyData = numpy.array(
		scipy.ndimage.measurements.minimum_position(
			fftcenter, angleArray, dataIntegers))

	if debug is True:
		fftcenter[xyData[:,0], xyData[:,1]] = maxVal*3
		showImage(fftcenter)

	ellipseParams = ellipse.totalLeastSquareEllipse(xyData, center=(xhalfshape, yhalfshape))
	if ellipseParams is None:
		return None
	ellipse.printParamsDict(ellipseParams)

	if debug is True:
		numPoints = int(math.pi*(ellipseParams['a']+ellipseParams['b']))
		ellPoints = ellipse.generate_ellipse(ellipseParams['a'], ellipseParams['b'], 
			ellipseParams['alpha'], center=ellipseParams['center'], numpoints=numPoints, integers=True)
		fftcenter[ellPoints[:,0], ellPoints[:,1]] += maxVal
		showImage(fftcenter)

	return ellipseParams


#=========================================
def rotationalAverage(image, ringwidth=3.0, innercutradius=None, full=False, median=False):
	"""
	compute the rotational average of a 2D numpy array

	full : False -- only average complete circles (no edges/corners)
	       True  -- rotational average out to corners of image

	median : False -- calculate the mean of each ring
	         True  -- calculate the median of each ring (slower)
	"""

	if debug is True:
		print "ring width %.2f pixels"%(ringwidth)

	shape = image.shape
	## create a grid of distance from the center
	xhalfshape = shape[0]/2.0
	x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
	yhalfshape = shape[1]/2.0
	y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
	xx, yy = numpy.meshgrid(x, y)
	radial = xx**2 + yy**2 - 0.5
	radial = numpy.sqrt(radial)

	## convert to integers
	radial = radial/ringwidth
	radial = numpy.array(radial, dtype=numpy.int32)
	if shape[0] < 32:
		print radial

	count = 0
	if debug is True:
		print "computing rotational average xdata..."
	xdataint = numpy.unique(radial)
	if full is False:
		### trims any edge artifacts from rotational average
		outercutsize = int((shape[0]/2-2)/ringwidth)
		if debug is True:
			apDisplay.printMsg("Num X points %d, Half image size %d, Trim size %d, Ringwidth %.2f, Percent trim %.1f"
				%(xdataint.shape[0], shape[0]/2-2, outercutsize, ringwidth, 100.*outercutsize/float(xdataint.shape[0])))
		if outercutsize > xdataint.shape[0]:
			apDisplay.printWarning("Outer cut radius is larger than X size")
		xdataint = xdataint[:outercutsize]

	if innercutradius is not None:
		innercutsize = int(math.floor(innercutradius/ringwidth))
		if debug is True:
			apDisplay.printMsg("Num X points %d, Half image size %d, Trim size %d, Ringwidth %.2f, Percent trim %.1f"
				%(xdataint.shape[0], shape[0]/2-2, innercutsize, ringwidth, 100.*innercutsize/float(xdataint.shape[0])))
		xdataint = xdataint[innercutsize:]
	
	### remove
	data = image.copy()

	if median is True:
		print "performing very slow median calculation loop on %d values"%(len(xdataint))
		for i in xdataint:
			median = numpy.median(data[radial == i])
			data[radial == i] = median

	if debug is True:
		print "computing rotational average ydata..."
	ydata = numpy.array(scipy.ndimage.mean(data, radial, xdataint))
	xdata = numpy.array(xdataint, dtype=numpy.float64)*ringwidth

	if debug is True:
		print "... finish rotational average"
		apDisplay.printMsg("  expected size of rotational average: %d"%(image.shape[0]/2))
		apDisplay.printMsg("actual max size of rotational average: %d"%(xdata.max())) 

	return xdata, ydata


#=========================================
#=========================================


