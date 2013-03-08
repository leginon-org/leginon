#!/usr/bin/env python

import math
import time
import numpy

from appionlib.apImage import imagestat

#===================
# ANGULAR FUNCTIONS
#===================

#===================
class Angular(object):
	def __init__(self, shape, xfreq=1.0, yfreq=1.0, center=True, flip=False):
		# setup
		if center is True:
			### distance from center
			self.center = numpy.array(shape, dtype=numpy.float64)/2.0 - 0.5
		else:
			### the upper-left edge
			self.center = (-0.5, -0.5)
		# function
		self.flip = flip
		self.xfreq = xfreq
		self.yfreq = yfreq
		self.angular = numpy.fromfunction(self.arctan, shape, dtype=numpy.float64)

	def arctan(self, y, x):
		dy = (y - self.center[0])*self.yfreq
		dx = (x - self.center[1])*self.xfreq
		if self.flip is True:
			dy = -1.0*numpy.fliplr(dy)
			dx = -1.0*dx
			#print "flipping"
		#print "dy", dy
		#print "dx", dx
		angle = numpy.arctan2(dy, dx)
		return angle

#===================
def generateAngular1(shape, xfreq, yfreq):
	"""
	this method is about 2x slower than method 2
	"""
	t0 = time.time()
	a = Angular(shape, xfreq, yfreq)
	angular = a.angular
	### raw radius from center
	#print numpy.around(angular*180/math.pi,1)
	print "angular 1 complete in %.4f sec"%(time.time()-t0)
	return angular

#===================
def generateAngular2(shape, xfreq, yfreq):
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
# RADIAL FUNCTIONS
#===================

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
def generateRadial1(shape, xfreq, yfreq):
	"""
	this method is about 4x slower than method 2
	"""
	t0 = time.time()
	r = Radial(shape, xfreq, yfreq)
	circular = r.radial
	### raw radius from center
	#print circular
	print "radial 1 complete in %.4f sec"%(time.time()-t0)
	return circular

#===================
def radiusfunc(x, y):
	radiussq = (x + 0.5)**2 + (y + 0.5)**2
	return radiussq

#===================
def generateRadial2(shape, xfreq=1.0, yfreq=1.0):
	"""
	this method is about 4x faster than method 1
	"""
	t0 = time.time()
	print shape
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
# GAUSSIAN FUNCTIONS
#===================


#===================
def generateGaussion1(shape, sigma=None):
	"""
	this method is about 4x slower than method 2
	"""
	t0 = time.time()
	if sigma is None:
		sigma = numpy.mean(shape)/4.0
	circular = generateRadial1(shape)
	circular = numpy.exp(-circular / sigma**2)
	print "gaussian 1 complete in %.4f sec"%(time.time()-t0)
	return circular

#===================
def generateGaussion2(shape, sigma=None):
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
#===================
#===================
if __name__ == "__main__":
	r = circle.Radial((7,11))
	a = r.radial
	print numpy.array(numpy.exp(-a/3)*1000, dtype=numpy.uint16)
