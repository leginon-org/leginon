#!/usr/bin/env python

import time
import math
import numpy
from appionlib import apDisplay
from appionlib.apCtf import ctftools

debug = False

#===================
def generateCTF1d(radii=None, focus=1.0e-6, cs=2e-3, volts=120000, ampconst=0.07, 
		failParams=False, overfocus=False):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Underfocus is postive (defocused) 
	"""
	if debug is True:
		print "generateCTF1dFromRadii()"

	if radii is None:
		radii = generateRadii1d(numpoints=256, pixelsize=1e-10)

	if debug is True:
		apDisplay.printColor("generateCTF radii: 1/%.2fA --> 1/%.2fA"%(1/radii[1]*1e10, 1/radii[-1]*1e10), "cyan")

	t0 = time.time()
	checkParams(focus1=focus, focus2=focus, cs=cs, volts=volts, ampconst=ampconst, failParams=failParams)

	lamb = ctftools.getTEMLambda(volts)
	s = radii
	pi = math.pi

	if overfocus is True:
		focus = -1.0*focus

	gamma = -0.5*pi*cs*(lamb**3)*(s**4) + pi*focus*lamb*(s**2)

	if overfocus is True:
		gamma = -1.0*gamma

	A = ampconst
	B = math.sqrt(1.0 - ampconst**2)
	prectf = A*numpy.cos(gamma) + B*numpy.sin(gamma)

	ctf = prectf**2

	if debug is True:
		print "generate 1D ctf complete in %.9f sec"%(time.time()-t0)

	return ctf

#===================
def getDiffResForOverfocus(radii=None, cs=2e-3, volts=120000):
	"""
	given Cs and kV, determine the initial resolution where the difference between
	overfocus and underfocus is clearly visible.

	value returned in Angstroms, but radii must be in meters
	"""

	if debug is True:
		print "getDiffResForOverfocus()"

	if debug is True:
		apDisplay.printColor("getDiffRes radii: 1/%.2fA --> 1/%.2fA"%(1/radii[1]*1e10, 1/radii[-1]*1e10), "cyan")

	t0 = time.time()
	checkParams(focus1=1.0e-6, focus2=1.0e-6, cs=cs, volts=volts, ampconst=0.0, failParams=False)


	lamb = ctftools.getTEMLambda(volts)
	s = radii
	pi = math.pi

	csgamma = 2*pi*0.25*cs*(lamb**3)*(s**4)
	
	#over/under-focus difference is visible when Cs component is greater than 0.05
	index = numpy.searchsorted(csgamma, 0.03)

	diffres = 1.0/radii[index-1]*1e10

	apDisplay.printColor("Overfocus/Underfocus difference resolution is: 1/%.2fA"%(diffres), "cyan")

	if debug is True:
		print "difference resolution complete in %.9f sec"%(time.time()-t0)
	return diffres

#===================
def generateCTF1dACE2(radii=None, focus=1.0e-6, cs=2e-3, volts=120000, ampconst=0.07, failParams=False):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Underfocus is postive (defocused) 
	"""
	if debug is True:
		print "generateCTF1dFromRadii()"
	t0 = time.time()
	checkParams(focus1=focus, focus2=focus, cs=cs, volts=volts, ampconst=ampconst, failParams=failParams)
	minres = 1e10/radii.min()
	maxres = 1e10/radii.max()
	if debug is True:
		print "** CTF limits %.1f A -->> %.1fA"%(minres, maxres)
	if maxres < 2.0 or maxres > 50.0:
		apDisplay.printError("CTF limits are incorrect %.1f A -->> %.1fA"%(minres, maxres))

	wavelength = ctftools.getTEMLambda(volts)

	x4 = math.pi/2.0 * wavelength**3 * cs
	x2 = math.pi * wavelength
	x0 = 1.0*math.asin(ampconst) #CORRECT
	if debug is True:
		print "x0 shift %.1f degrees"%(math.degrees(x0))

	radiisq = radii**2

	gamma = (x4 * radiisq**2) + (-focus * x2 * radiisq) + (x0)
	#ctf = -1.0*numpy.cos(gamma) #WRONG
	#ctf = -1.0*numpy.sin(gamma) #CORRECT
	ctf = 1.0*numpy.sin(gamma) #MAYBE CORRECT

	if debug is True:
		print "generate 1D ctf complete in %.9f sec"%(time.time()-t0)

	return ctf**2

#===================
def generateCTF1dMakePoints(numpoints=256, focus=1.0e-6, 
	pixelsize=1.5e-10, cs=2e-3, volts=120000, ampconst=0.07):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Underfocus is postive (defocused) 
	"""
	if debug is True:
		print "generateCTF1d()"
	checkParams(focus1=focus, focus2=focus, pixelsize=pixelsize, cs=cs, 
		volts=volts, ampconst=ampconst)

	radii = generateRadii1d(numpoints, pixelsize)

	ctf = generateCTF1dFromRadii(radii, focus, cs, volts, ampconst)

	return ctf

#===================
def generateRadii1d(numpoints=256, pixelsize=1e-10):
	radfreq = 1.0/( numpoints*pixelsize )
	radii = numpy.arange(numpoints) * radfreq
	return radii

#===================
def generateCTF2d(focus1=-1.0e-6, focus2=-1.0e-6, theta=0.0, 
	shape=(256,256), pixelsize=1.0e-10, cs=2e-3, volts=120000, ampconst=0.000):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Underfocus is postive (defocused) 
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

	if debug is True:
		print "generate ctf 2d complete in %.4f sec"%(time.time()-t0)

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
def checkParams(focus1=-1.0e-6, focus2=-1.0e-6, pixelsize=1.5e-10, 
	cs=2e-3, volts=120000, ampconst=0.07, failParams=False):
	if debug is True:
		print "  Defocus1 %.2f microns (underfocus is positive)"%(focus1*1e6)
		if focus1 != focus2:
			print "  Defocus2 %.2f microns (underfocus is positive)"%(focus2*1e6)
		print "  Pixelsize %.3f Angstroms"%(pixelsize*1e10)
		print "  C_s %.1f mm"%(cs*1e3)
		print "  High tension %.1f kV"%(volts*1e-3)
		print ("  Amp Contrast %.3f (shift %.1f degrees)"
			%(ampconst, math.degrees(-math.asin(ampconst))))
	if focus1*1e6 > 15.0 or focus1*1e6 < 0.1:
		msg = "atypical defocus #1 value %.1f microns (underfocus is positve)"%(focus1*1e6)
		if failParams is False:
			apDisplay.printWarning(msg)
		else:
			apDisplay.printError(msg)
	if focus2*1e6 > 15.0 or focus2*1e6 < 0.1:
		msg = "atypical defocus #2 value %.1f microns (underfocus is positve)"%(focus2*1e6)
		if failParams is False:
			apDisplay.printWarning(msg)
		else:
			apDisplay.printError(msg)
	if cs*1e3 > 7.0 or cs*1e3 < 0.0:
		msg = "atypical C_s value %.1f mm"%(cs*1e3)
		if failParams is False:
			apDisplay.printWarning(msg)
		else:
			apDisplay.printError(msg)
	if pixelsize*1e10 > 20.0 or pixelsize*1e10 < 0.1:
		msg = "atypical pixel size value %.1f Angstroms"%(pixelsize*1e10)
		if failParams is False:
			apDisplay.printWarning(msg)
		else:
			apDisplay.printError(msg)
	if volts*1e-3 > 400.0 or volts*1e-3 < 60:
		msg = "atypical high tension value %.1f kiloVolts"%(volts*1e-3)
		if failParams is False:
			apDisplay.printWarning(msg)
		else:
			apDisplay.printError(msg)
	if ampconst < 0.0 or ampconst > 0.5:
		msg = "atypical amplitude contrast value %.3f"%(ampconst)
		if failParams is False:
			apDisplay.printWarning(msg)
		else:
			apDisplay.printError(msg)
	return

#===================
#===================
#===================
if __name__ == "__main__":
	r = generateRadial2d((8,8), 0.1, 0.1)
	radii = generateRadii1d()
	ctf = generateCTF1d(radii)
	from matplotlib import pyplot
	pyplot.plot(radii, ctf, 'r-', )
	pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
		bottom=0.05, left=0.05, top=0.95, right=0.95, )
	pyplot.show()


