#!/usr/bin/env python

import time
import math
import numpy
from appionlib import apDisplay
from appionlib.apCtf import ctftools

debug = False

#===================
def generateCTF1d(radii=None, focus=-1.0e-6, numpoints=256, 
	pixelsize=1.5e-10, cs=2e-3, volts=120000, ampconst=0.07):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Focus is negative, if under focused (defocused) 
	"""
	t0 = time.time()

	wavelength = ctftools.getTEMLambda(volts)

	ctf = numpy.zeros((numpoints), dtype=numpy.float64)

	t1 = math.pi * wavelength
	t2 = wavelength**2 * cs / 2.0
	t3 = -1.0*math.asin(ampconst)

	if radii is None:
		radii = generateRadii1d(numpoints, pixelsize)
	radiisq = radii**2

	gamma = t1*radiisq * (focus + t2*radiisq) + t3
	ctf = -1.0*numpy.sin(gamma)

	print "generate 1D ctf complete in %.4f sec"%(time.time()-t0)

	return ctf

#===================
def generateRadii1d(numpoints=256, pixelsize=1e-10):
	radfreq = 1.0/( (numpoints-1)*2.*pixelsize )
	radii = numpy.arange(numpoints) * radfreq
	return radii

#===================
def generateCTF2d(focus1=-1.0e-6, focus2=-1.0e-6, theta=0.0, 
	shape=(256,256), pixelsize=1.0e-10, cs=2e-3, volts=120000, ampconst=0.000):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Focus is negative, if under focused (defocused) 
	"""
	t0 = time.time()

	wavelength = getTEMLambda(volts)

	xfreq = 1.0/( (shape[1]-1)*2.*pixelsize )
	yfreq = 1.0/( (shape[0]-1)*2.*pixelsize )

	ctf = numpy.zeros(shape, dtype=numpy.float64)

	meanfocus = (focus1 + focus2) / 2.
	focusdiff = (focus1 - focus2) / 2. 

	t1 = math.pi * wavelength
	t2 = wavelength**2 * cs / 2.0
	t3 = -1.0*math.asin(ampconst)

	radiisq = circle.generateRadial1d(shape, xfreq, yfreq)
	angles = -circle.generateAngular2d(shape, xfreq, yfreq)
	localfocus = meanfocus + focusdiff * numpy.cos(2.0*(angles-theta))
	gamma = t1*radiisq * (-localfocus + t2*radiisq) + t3
	ctf = numpy.sin(gamma)

	gauss = circle.generateGaussion2d(shape)
	imagefile.arrayToJpeg(gauss, "gauss2.jpg")

	print "generate ctf 2 complete in %.4f sec"%(time.time()-t0)

	return ctf*gauss

#===================
def generateAngular2d(shape, xfreq, yfreq):
	"""
	this method is about 2x faster than method 1
	"""
	t0 = time.time()
	if shape[0] % 2 != 0 or shape[1] % 2 != 0:
		apDisplay.printError("array shape for radial function must be even")

	halfshape = numpy.array(shape)/2.0
	a = Angular(halfshape, xfreq, yfreq, center=False, flip=False)
	angular1 = a.angular
	b = Angular(halfshape, xfreq, yfreq, center=False, flip=True)
	angular2 = numpy.fliplr(b.angular)
	circular = numpy.vstack( 
		(numpy.hstack( 
			(numpy.flipud(angular2), -numpy.flipud(angular1))
		),numpy.hstack( 
			(-angular2, angular1), 
		)))

	### raw radius from center
	#print numpy.around(circular*180/math.pi,1)
	print "angular 2 complete in %.4f sec"%(time.time()-t0)
	return circular

#===================
def generateGaussion2d(shape, sigma=None):
	"""
	this method is about 4x faster than method 1
	"""
	t0 = time.time()
	if sigma is None:
		sigma = numpy.mean(shape)/4.0
	circular = generateRadial2(shape)
	circular = numpy.exp(-circular/sigma**2)
	print "gaussian 2 complete in %.4f sec"%(time.time()-t0)
	return circular

#===================
class Radial(object):
	def __init__(self, shape, xfreq=1.0, yfreq=1.0, center=True):
		# setup
		if center is True:
			### distance from center
			self.center = numpy.array(shape, dtype=numpy.float64)/2.0 - 0.5
		else:
			### the upper-left edge
			self.center = (-0.5, -0.5)
		self.xfreqsq = xfreq**2
		self.yfreqsq = yfreq**2
		# function
		self.radial = numpy.fromfunction(self.distance, shape, dtype=numpy.float64)

	def distance(self, y, x):
		distance = (
			(x - self.center[1])**2 * self.xfreqsq 
			+ (y - self.center[0])**2 * self.yfreqsq
		)
		return distance

#===================
def generateRadial2d(shape, xfreq, yfreq):
	"""
	this method is about 4x faster than method 1
	"""
	t0 = time.time()
	if shape[0] % 2 != 0 or shape[1] % 2 != 0:
		apDisplay.printError("array shape for radial function must be even")

	halfshape = numpy.array(shape)/2.0
	#radial = numpy.fromfunction(radiusfunc, halfshape)
	r = Radial(halfshape, xfreq, yfreq, center=False)
	radial = r.radial
	circular = numpy.vstack( 
		(numpy.hstack( 
			(numpy.fliplr(numpy.flipud(radial)), numpy.flipud(radial))
		),numpy.hstack( 
			(numpy.fliplr(radial), radial), 
		)))
	### raw radius from center
	#print circular
	print "radial 2 complete in %.4f sec"%(time.time()-t0)
	return circular


#===================
#===================
#===================
if __name__ == "__main__":
	r = generateRadial2d((8,8), 0.1, 0.1)
	radii = generateRadii1d()
	ctf = generateCTF1d(radii)
	from matplotlib import pyplot
	pyplot.plot(radii, ctf, 'r-', )
	pyplot.show()


