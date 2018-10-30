#!/usr/bin/env python

import time
import math
import numpy
import scipy.ndimage
from appionlib import apDisplay
from appionlib.apCtf import ctftools
from appionlib.apImage import imagestat

###this file is not allowed to import any apCtf files, besides ctftools

debug = False

#===================
def generateCTF1d(radii=None, focus=1.0e-6, cs=2e-3, volts=120000, ampconst=0.07, extra_phase_shift=0.0, 
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
	checkParams(focus1=focus, focus2=focus, cs=cs, volts=volts, ampconst=ampconst, extra_phase_shift=extra_phase_shift, failParams=failParams)

	lamb = ctftools.getTEMLambda(volts)
	s = radii
	pi = math.pi

	if overfocus is True:
		focus = -1.0*focus

	gamma = -0.5*pi*cs*(lamb**3)*(s**4) + pi*focus*lamb*(s**2) + extra_phase_shift

	#if overfocus is True:
	#	gamma = -1.0*gamma

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
	checkParams(focus1=1.0e-6, focus2=1.0e-6, cs=cs, volts=volts, ampconst=0.0, extra_phase_shift=0.0, failParams=False)


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
def generateCTF1dACE2(radii=None, focus=1.0e-6, cs=2e-3, volts=120000, ampconst=0.07, extra_phase_shift=0.0, failParams=False):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Underfocus is postive (defocused) 
	"""
	if debug is True:
		print "generateCTF1dFromRadii()"
	t0 = time.time()
	checkParams(focus1=focus, focus2=focus, cs=cs, volts=volts, ampconst=ampconst, extra_phase_shift=0.0, failParams=failParams)
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

	#this gamma has the opposide sign of the others
	gamma = (x4 * radiisq**2) + (-focus * x2 * radiisq) + (x0) - extra_phase_shift
	#ctf = -1.0*numpy.cos(gamma) #WRONG
	#ctf = -1.0*numpy.sin(gamma) #CORRECT
	ctf = 1.0*numpy.sin(gamma) #MAYBE CORRECT

	if debug is True:
		print "generate 1D ctf complete in %.9f sec"%(time.time()-t0)

	return ctf**2

#===================
def generateRadii1d(numpoints=256, pixelsize=1e-10):
	radfreq = 1.0/( numpoints*pixelsize )
	radii = numpy.arange(numpoints) * radfreq
	return radii

#===================
def generateCTF2dFromCtfData(ctfdata, apix, volts, fieldsize):
	focus1 = ctfdata['defocus1']
	focus2 = ctfdata['defocus2']
	theta = math.radians(ctfdata['angle_astigmatism']) #radians, new oops fix??
	extra_phase_shift = ctfdata['extra_phase_shift'] # radians
	mpix = apix*1e-10
	cs = ctfdata['cs']*1e-3
	volts = volts
	ampconst = ctfdata['amplitude_contrast']
	shape = (fieldsize, fieldsize)
	checkParams(focus1=focus1, focus2=focus2, cs=cs, volts=volts, ampconst=ampconst, extra_phase_shift=extra_phase_shift, failParams=False)
	return generateCTF2d(focus1, focus2, theta, shape, mpix, cs, volts, ampconst, extra_phase_shift)

#===================
def generateCTF2d(focus1=-1.0e-6, focus2=-1.0e-6, theta=0.0, 
	shape=(256,256), pixelsize=1.0e-10, cs=2e-3, volts=120000, ampconst=0.000, extra_phase_shift=0.0):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Underfocus is postive (defocused) 
	"""
	t0 = time.time()
	if debug is True:
		from appionlib.apImage import imagestat

	gamma = generateGamma2d(focus1, focus2, theta, shape, pixelsize, cs, volts, ampconst, extra_phase_shift)

	"""
	#gamma = t1*radiisq * (-localfocus + t2*radiisq) + t3
	A = ampconst
	B = math.sqrt(1.0 - ampconst**2)
	prectf = A*numpy.cos(gamma) + B*numpy.sin(gamma)
	ctf = prectf**2
	"""

	prectf = numpy.sin(gamma)
	ctf = prectf**2

	if debug is True:
		print "\n CTF"
		imagestat.printImageInfo(ctf)

	if debug is True:
		print "generate ctf 2d complete in %.4f sec"%(time.time()-t0)

	return ctf

#===================
def generateLocalFocus2d(focus1=-1.0e-6, focus2=-1.0e-6, theta=0.0, shape=(256,256)):
	t0 = time.time()
	if debug is True:
		from appionlib.apImage import imagestat

	meanfocus = (focus1 + focus2) / 2.
	focusdiff = (focus1 - focus2) / 2. 

	angles = -1*generateAngular2d(shape)
	if debug is True:
		print "\n ANGLES"
		imagestat.printImageInfo(angles)

	localfocus = meanfocus + focusdiff * numpy.cos(2.0*(angles-theta))

	if debug is True:
		print "generate local focus 2d complete in %.4f sec"%(time.time()-t0)

	return localfocus

#===================
def generateGamma2d(focus1=-1.0e-6, focus2=-1.0e-6, theta=0.0, 
	shape=(256,256), pixelsize=1.0e-10, cs=2e-3, volts=120000, ampconst=0.000, extra_phase_shift=0.0):
	"""
	calculates a CTF function based on the input details

	Use SI units: meters, radians, volts
	Underfocus is postive (defocused) 
	"""
	t0 = time.time()
	if debug is True:
		from appionlib.apImage import imagestat

	wavelength = ctftools.getTEMLambda(volts)

	xfreq = 1.0/( (shape[1]-1)*2.*pixelsize )
	yfreq = 1.0/( (shape[0]-1)*2.*pixelsize )

	#t1 = math.pi * wavelength
	#t2 = wavelength**2 * cs / 2.0
	#t3 = -1.0*math.asin(ampconst)

	radiisq = generateRadial2d(shape, xfreq, yfreq)
	if debug is True:
		print "\n RADII"
		imagestat.printImageInfo(1.0/numpy.sqrt(radiisq))
	if debug is True:
		halfshape = shape[0]/2
		apDisplay.printColor("generateCTF 2d radii: 1/%.2fA --> 1/%.2fA"
			%(1/math.sqrt(radiisq[halfshape,halfshape])*1e10, 1/math.sqrt(radiisq[0,halfshape])*1e10), "cyan")

	angles = -1*generateAngular2d(shape)
	if debug is True:
		print "\n ANGLES"
		imagestat.printImageInfo(angles)

	localfocus = generateLocalFocus2d(focus1, focus2, theta, shape)
	if debug is True:
		print "\n FOCUS"
		imagestat.printImageInfo(localfocus*1e6)

	x4 = -math.pi/2.0 * wavelength**3 * cs
	x2 = math.pi * wavelength
	x0 = math.asin(ampconst) + extra_phase_shift
	if debug is True:
		print "x0 shift %.1f degrees"%(math.degrees(x0))

	gamma1 = (x4 * radiisq**2) + (localfocus * x2 * radiisq) + (x0) 

	"""
	#ctf = -1.0*numpy.cos(gamma) #WRONG
	#ctf = -1.0*numpy.sin(gamma) #CORRECT
	prectf1 = 1.0*numpy.sin(gamma1) #MAYBE CORRECT
	ctf1 = prectf1**2

	gamma2 = -0.5*math.pi*cs*(wavelength**3)*(radiisq**2) + math.pi*localfocus*wavelength*(radiisq) + extra_phase_shift
	if debug is True:
		print "\n GAMMA"
		imagestat.printImageInfo(gamma2)

	#gamma = t1*radiisq * (-localfocus + t2*radiisq) + t3
	A = ampconst
	B = math.sqrt(1.0 - ampconst**2)
	prectf = A*numpy.cos(gamma2) + B*numpy.sin(gamma2)
	ctf2 = prectf**2
	"""

	if debug is True:
		print "generate gamma 2d complete in %.4f sec"%(time.time()-t0)

	return gamma1

#============
def equiPhaseAverage(image, ellipratio,
		focus1, focus2, angle, pixelsize, cs, volts, ampconst, extra_phase_shift,
		ringwidth=2.0, innercutradius=None, full=False):
	"""
	compute the equiphase average of a 2D numpy array

	full : False -- only average complete circles (no edges/corners)
	       True  -- rotational average out to corners of image

	median : False -- calculate the mean of each ring
	         True  -- calculate the median of each ring (slower)
	"""
	#normally this would be in ctftools, but we need the functions from this file
	if debug is True:
		print "ring width %.2f pixels"%(ringwidth)
		print "angle = ", angle
		print "cs = ", cs
		print "volts = ", volts
		print "ampconst = ", ampconst
		print "extra_phase_shift = ", extra_phase_shift

	theta = math.radians(angle)

	checkParams(focus1=focus1, focus2=focus2, pixelsize=pixelsize, cs=cs, volts=volts,
		ampconst=ampconst, extra_phase_shift=extra_phase_shift, failParams=True)

	wavelength = ctftools.getTEMLambda(volts)
	localfocus = generateLocalFocus2d(focus1, focus2, theta, image.shape)

	shape = image.shape
	gamma = generateGamma2d(focus1, focus2, theta, shape, pixelsize, cs, volts, ampconst, extra_phase_shift)
	maxval = max(shape)/math.sqrt(2.0)
	if abs(gamma.min()) > 0.1:
		apDisplay.printWarning("Gamma has a larger value than expected")
	#this makes the distribution more radial-like, not sure if it is better

	x4 = -math.pi/2.0 * wavelength**3 * cs
	x2 = math.pi * wavelength
	x0 = math.asin(ampconst) + extra_phase_shift

	## gamma = x4 * s^4  +  x2 * z * s^2  +  x0 
	## x4 * s^4  +  x2 * z * s^2  +  x0 - gamma = 0
	## quadratic formula
	## s^2 = (-x2*z +- sqrt[x2^2 z^2 - 4 x4 x0] ) / (2 x4)

	## discriminant = b^2 - 4ac ==> x2^2 z^2 - 4 x4 x0
	discriminant = x2**2 * localfocus**2  -  4 * x4 * (x0 - gamma)
	sprime = numpy.sqrt( (-1.0 * x2 * localfocus + numpy.sqrt(discriminant)) / (2 * x4) )

	imagestat.printImageInfo(sprime)
	#gamma = gamma**2
	## scale to pixel units
	sprime -= (sprime.min() - 0.01)
	sprime *= (maxval / sprime.max())

	if debug is True:
		print "sprime"
		imagestat.printImageInfo(sprime)

		radial = ctftools.getEllipticalDistanceArray(1, 0, image.shape)
		print "radial"
		imagestat.printImageInfo(radial)
		
		from pyami import mrc
		mrc.write(radial, "radial.mrc")
		mrc.write(sprime, "sprime.mrc")
		print "diff = "
		diff = sprime - radial
		mrc.write(diff, "diff.mrc")
		imagestat.printImageInfo(diff)

	## adjust size of averaging rings, in Fourier pixels
	sprime = sprime/ringwidth
	## need to convert to integers for scipy labels function
	sprime = numpy.array(sprime, dtype=numpy.int32)

	if debug is True:
		print "computing equiphase average xdata..."

	xdataint = numpy.unique(sprime)
	if debug is True:
		print "pre-edit xdataint", xdataint[:5], "..", xdataint[-5:] 
		imagestat.printImageInfo(xdataint)

	bigshape = numpy.array(numpy.array(image.shape)*math.sqrt(2)/2., dtype=numpy.int)*2
	if full is False:
		### trims any edge artifacts from rotational average
		outercutsize = int((bigshape[0]/2-2)/ringwidth*math.sqrt(2)/2.)
		if debug is True:
			apDisplay.printColor("Num X points %d, Half image size %d, Outer cut size %d, Ringwidth %.2f, Percent trim %.1f"
				%(xdataint.shape[0], bigshape[0]/2-2, outercutsize, ringwidth, 100.*outercutsize/float(xdataint.shape[0])), "yellow")
		if outercutsize > xdataint.shape[0]:
			apDisplay.printWarning("Outer cut radius is larger than X size")
		xdataint = xdataint[:outercutsize]

	if innercutradius is not None:
		innercutsize = int(math.floor(innercutradius/ringwidth))
		if debug is True:
			apDisplay.printMsg("Num X points %d, Half image size %d, Trim size %d, Ringwidth %.2f, Percent trim %.1f"
				%(xdataint.shape[0], bigshape[0]/2-2, innercutsize, ringwidth, 100.*innercutsize/float(xdataint.shape[0])))
		xdataint = xdataint[innercutsize:]

	if debug is True:
		print "edited xdataint", xdataint[:5], "..", xdataint[-5:] 
		imagestat.printImageInfo(xdataint)

	### remove
	data = image.copy()
	if debug is True:
		print "raw data"
		imagestat.printImageInfo(data)
	if numpy.any(numpy.isnan(data)):
		print data
		apDisplay.printError("Major Error (NaN) in equiphase average, data")

	if debug is True:
		print "computing equiphase average ydata..."
	ydata = numpy.array(scipy.ndimage.mean(data, sprime, xdataint))
	if debug is True:
		print "ydata"
		imagestat.printImageInfo(ydata)
	if len(ydata) == 0:
		print "ydata", ydata
		apDisplay.printWarning("Major Error: nothing returned for equiphase average, ydata")
		return None, None

	### WHAT ARE YOU DOING WITH THE SQRT ellipratio??? It just works
	xdata = numpy.array(xdataint, dtype=numpy.float64)*ringwidth/math.sqrt(ellipratio)
	if debug is True:
		print "xdata"
		imagestat.printImageInfo(xdata)

	if numpy.any(numpy.isnan(xdata)):  #note does not work with 'is True'
		print xdata
		apDisplay.printError("Major Error (NaN) in equiphase average, xdata")
	if numpy.any(numpy.isnan(ydata)):  #note does not work with 'is True'
		print ydata
		apDisplay.printError("Major Error (NaN) in equiphase average, ydata")

	if debug is True:
		print "... finish equiphase average"
		apDisplay.printMsg("  expected size of equiphase average: %d"%(bigshape[0]/2))
		apDisplay.printMsg("actual max size of equiphase average: %d"%(xdata.max())) 

	return xdata, ydata

#===================
class Angular(object):
	def __init__(self, shape, center=True, flip=False):
		# setup
		if center is True:
			### distance from center
			self.center = numpy.array(shape, dtype=numpy.float64)/2.0 - 0.5
		else:
			### the upper-left edge
			self.center = (-0.5, -0.5)
		# function
		self.flip = flip
		# fix for numpy 1.12 or newer
		shape = numpy.array(shape, dtype=numpy.uint16)
		self.angular = numpy.fromfunction(self.arctan, shape, dtype=numpy.float64)

	def arctan(self, y, x):
		dy = (y - self.center[0])
		dx = (x - self.center[1])
		if self.flip is True:
			dy = -1.0*numpy.fliplr(dy)
			dx = -1.0*dx
			#print "flipping"
		#print "dy", dy
		#print "dx", dx
		angle = numpy.arctan2(dy, dx)
		return angle

#===================
def generateAngular2d(shape):
	"""
	this method is about 2x faster than method 1
	"""
	t0 = time.time()
	if shape[0] % 2 != 0 or shape[1] % 2 != 0:
		apDisplay.printError("array shape for radial function must be even")

	halfshape = numpy.array(shape)/2.0
	a = Angular(halfshape, center=False, flip=False)
	angular1 = a.angular
	b = Angular(halfshape, center=False, flip=True)
	angular2 = numpy.fliplr(b.angular)
	circular = numpy.vstack( 
		(numpy.hstack( 
			(numpy.flipud(angular2), -numpy.flipud(angular1))
		),numpy.hstack( 
			(-angular2, angular1), 
		)))

	### raw radius from center
	#print numpy.around(circular*180/math.pi,1)
	if debug is True:
		print "angular 2 complete in %.4f sec"%(time.time()-t0)
	return circular

#===================
def generateGaussion2d(shape, xfreq, yfreq, sigma=None):
	"""
	this method is about 4x faster than method 1
	"""
	t0 = time.time()
	if sigma is None:
		sigma = numpy.mean(shape)/4.0
	circular = generateRadial2d(shape, xfreq, yfreq)
	circular = numpy.exp(-circular/sigma**2)
	if debug is True:
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
		# fix for numpy 1.12 or newer
		shape = numpy.array(shape, dtype=numpy.uint16)
		# function
		self.radial = numpy.fromfunction(self.distance, shape, dtype=numpy.float64)

	def distance(self, y, x):
		dist = (
			(x - self.center[1])**2 * self.xfreqsq 
			+ (y - self.center[0])**2 * self.yfreqsq
		)
		return dist

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
	if debug is True:
		print "radial 2 complete in %.4f sec"%(time.time()-t0)
	return circular

#===================
def checkParams(focus1=-1.0e-6, focus2=-1.0e-6, pixelsize=1.5e-10, 
	cs=2e-3, volts=120000, ampconst=0.07, extra_phase_shift=0.0, failParams=False):
	if debug is True:
		print "  Defocus1 %.2f microns (underfocus is positive)"%(focus1*1e6)
		if focus1 != focus2:
			print "  Defocus2 %.2f microns (underfocus is positive)"%(focus2*1e6)
		print "  Pixelsize %.3f Angstroms"%(pixelsize*1e10)
		print "  C_s %.1f mm"%(cs*1e3)
		print "  High tension %.1f kV"%(volts*1e-3)
		print ("  Amp Contrast %.3f (shift %.1f degrees)"
			%(ampconst, math.degrees(-math.asin(ampconst))))
		print ("  Extra Phase Shift  %.1f degrees"
			% (math.degrees(extra_phase_shift)))
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


