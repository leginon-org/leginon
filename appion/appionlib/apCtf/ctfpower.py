#!/usr/bin/env python

import time
import math
import numpy
from pyami import mrc
from pyami import imagefun
from appionlib import apDisplay
from appionlib.apImage import imagestat, imagefile, imagefilter

debug = True

#============
def funcrad(x, xdata=None, ydata=None):
	return numpy.interp(x, xdata, ydata)

#=============
def twodHann(size):
	rsize = int(math.ceil(size*math.sqrt(2)))
	xdata = numpy.arange(rsize)+0.5
	xdata = xdata - xdata.mean()
	ydata = numpy.hanning(rsize)
	#ydata = numpy.hstack(([1], ydata))
	hanntwod = imagefun.fromRadialFunction(funcrad, (size,size), xdata=xdata, ydata=ydata)
	return hanntwod

#=============
def getFieldSize(shape):
	mindim = min(shape)
	twopower = math.log(float(mindim))/math.log(2.0)
	fieldsize = 2**(math.floor(twopower-0.9))
	if debug is True:
		print "mindim=", mindim
		print "twopower=", twopower
		print "fieldsize=", fieldsize
	return fieldsize

#=============
def power(image, pixelsize, fieldsize=None, mask_radius=0.2):
	"""
	computes power spectra of image using sub-field averaging

	image - (2d numpy float array) image to compute power spectra
	pixelsize - (float) used to compute frequency, freq. 
		can be either Angstroms or meters, but freq will have same inverse units
	fieldsize - (integer) size of box
	mask_radius - (float) passed to imagefun.power(), 
		creates a mask of size mask_radius in the center

	TODO: add median flag, requires saving individual power spectra rather than summing
	"""
	if fieldsize is None:
		fieldsize = getFieldSize(image.shape)

	t0 = time.time()
	xsize, ysize = image.shape
	xstep = int(math.floor(xsize/float(fieldsize*2)))
	ystep = int(math.floor(ysize/float(fieldsize*2)))
	f = fieldsize
	powersum = numpy.zeros((fieldsize,fieldsize))
	#envelop = numpy.ones((fieldsize,fieldsize)) 
	envelop = twodHann(fieldsize)
	count = 0
	for i in range(xstep):
		for j in range(ystep):
			count += 1
			x1 = f*i
			x2 = f*(i+1)
			y1 = f*j
			y2 = f*(j+1)
			#print "%03d: %d:%d, %d:%d"%(count, x1, x2, y1, y2)
			cutout = image[x1:x2, y1:y2]
			powerspec = imagefun.power(cutout*envelop, mask_radius)
			powersum += powerspec
	if xsize%fieldsize > fieldsize*0.1:
		for j in range(ystep):
			count += 1
			x1 = xsize-f
			x2 = xsize
			y1 = f*j
			y2 = f*(j+1)
			#print "%03d: %d:%d, %d:%d"%(count, x1, x2, y1, y2)
			cutout = image[x1:x2, y1:y2]
			powerspec = imagefun.power(cutout*envelop, mask_radius)
			powersum += powerspec
	if ysize%fieldsize > fieldsize*0.1:
		for i in range(xstep):
			count += 1
			x1 = f*i
			x2 = f*(i+1)
			y1 = ysize-f
			y2 = ysize
			#print "%03d: %d:%d, %d:%d"%(count, x1, x2, y1, y2)
			cutout = image[x1:x2, y1:y2]
			powerspec = imagefun.power(cutout*envelop, mask_radius)
			powersum += powerspec
	freq = 1.0/(powerspec.shape[0]*pixelsize)

	poweravg = powersum/float(count)
	if debug is True:
		apDisplay.printMsg("fieldsize %d with %d images complete in %s"
			%(fieldsize, count, apDisplay.timeString(time.time()-t0)))
	return poweravg, freq

#===================
#===================
#===================
if __name__ == "__main__":
	a = mrc.read("/home/vosslab/test.mrc")
	a = imagefilter.planeRegression(a)
	fullpower = imagefun.power(a)
	#imagestat.printImageInfo(a)
	t0 = time.time()
	x = numpy.arange(6, 13)
	N = 2**x
	print N
	for n in N:
		print "====================================="
		b = power(a, n)
		b = imagefilter.frame_cut(b, numpy.array(b.shape)/2)
		imagefile.arrayToPng(b, "%04d-field.png"%(n))
		imagestat.printImageInfo(b)

		bin = int(round(2**12/n))
		b = imagefun.bin2(fullpower, bin)
		b = imagefilter.frame_cut(b, numpy.array(b.shape)/2)
		imagefile.arrayToPng(b, "%04d-binned.png"%(n))
		imagestat.printImageInfo(b)

	print "complete in %s"%(apDisplay.timeString(time.time()-t0))
	#imagestat.printImageInfo(b)
