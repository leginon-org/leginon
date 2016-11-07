#!/usr/bin/env python

import numpy
from pyami import mrc
from pyami import correlator

#=========================
def asymmetricalImage(boxsize):
	baseImage = numpy.zeros((boxsize,boxsize), dtype=numpy.uint16)
	ind = numpy.arange(0,11,1, dtype=numpy.float32)*boxsize/10.
	ind = numpy.array(numpy.round(ind), dtype=numpy.uint16)
	baseImage[ind[2]:ind[8],ind[2]:ind[8]] = 1
	baseImage[ind[1]:ind[2],ind[5]:ind[7]] = 1
	baseImage[ind[3]:ind[5],ind[1]:ind[2]] = 1
	baseImage[ind[8]:ind[9],ind[3]:ind[4]] = 1
	baseImage[ind[2]:ind[3],ind[2]:ind[3]] = 0
	baseImage[ind[2]:ind[3],ind[7]:ind[8]] = 0
	baseImage[ind[3]:ind[5],ind[4]:ind[6]] = 0
	baseImage[ind[5]:ind[6],ind[2]:ind[3]] = 0
	baseImage[ind[7]:ind[8],ind[4]:ind[6]] = 0
	return baseImage

#=========================
def sigmoidImage(boxsize, fuzzyVal=4):
	radial = distanceArray(boxsize)
	radial -= radial.min()
	edgeVal = radial[0,boxsize//2]
	radial /= edgeVal
	radial = 2*fuzzyVal*radial - fuzzyVal
	sigmoid = 1.0 / (1.0 + numpy.exp(radial))
	return sigmoid

#=========================
def distanceArray(boxsize):
	if boxsize % 2 != 0:
		raise ValueError
	shape = (boxsize, boxsize)
	xhalfshape = shape[0]/2.0
	x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
	yhalfshape = shape[1]/2.0
	y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
	xx, yy = numpy.meshgrid(x, y)
	radial = xx**2 + yy**2 - 0.5
	radial = numpy.sqrt(radial)
	return radial

#=========================
def eightTransforms(a):
	b = a.copy()
	t = []
	t.append(b)
	for i in range(3):
		b = numpy.rot90(b)
		t.append(b.copy())
	m = [] #mirrors
	for c in t:
		c = numpy.fliplr(c)
		m.append(c.copy())
	t.extend(m)
	return t

#=========================
def transformFromNumber(a, tnum):
	"""
	tnum in range 0 to 7
	"""
	if tnum == 0:
		return a
	if tnum == 1:
		return numpy.rot90(a)
	if tnum == 2:
		return numpy.rot90(a, 2)
	if tnum == 3:
		return numpy.rot90(a, 3)
	if tnum == 4:
		return numpy.fliplr(a)
	if tnum == 5:
		return numpy.rot90(numpy.fliplr(a))
	if tnum == 6:
		return numpy.rot90(numpy.fliplr(a), 2)
	if tnum == 7:
		return numpy.rot90(numpy.fliplr(a), 3)
	raise Exception("invalid tnum")

#=========================
def getEightTransforms(box, avgArray=None):
	"""
	correlate image with several permuations
	"""
	asymmArray = asymmetricalImage(box)
	if avgArray is not None:
		asymmArray = (asymmArray + avgArray)/2
	transformList = eightTransforms(asymmArray)
	return transformList

#=========================
def eightCorrelationTree(imgtree, avgArray=None):
	"""
	correlate list of images with several permuations
	"""
	box = max(imgtree[0])
	asymmArray = asymmetricalImage(box)
	if avgArray is not None:
		asymmArray = (asymmArray + avgArray)/2
	transformList = eightTransforms(asymmArray)
	sigArray = sigmoidImage(box)
	correlations = []
	for i, b in enumerate(transformList):
		rawcorr = correlator.cross_correlate(imgarray, b)
		rawcorr = numpy.fft.fftshift(rawcorr)
		finalcorr = rawcorr*sigArray
		correlations.append(finalcorr)
	return correlations

#=========================
#=========================
#=========================
if __name__ == '__main__':
	box = 12
	a = asymmetricalImage(box)
	t = eightTransforms(a)
	s = sigmoidImage(box)
	for i,b in enumerate(t):
		print b
		print ""
		mrc.write(b, "file%d.mrc"%(i))
		c = correlator.cross_correlate(a,b)
		c = numpy.fft.fftshift(c)
		#print numpy.round(c, 1)
		d = c*s
		print numpy.round(d, 1)
		
		
