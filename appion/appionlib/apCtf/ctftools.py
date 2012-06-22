#!/usr/bin/env python

import math
import numpy
import scipy.ndimage
from PIL import Image
from PIL import ImageDraw
from pyami import imagefun
from pyami import ellipse
from appionlib import apPrimeFactor
from appionlib import apDisplay
from appionlib.apImage import imagefile
from appionlib.apImage import imagefilter
#from appionlib import lowess

debug = False

#===================
def getCtfExtrema(focus=1.0e-6, pixelsize=1.0e-10, cs=2e-2, 
		volts=120000, ampconst=0.000, numzeros=3, cols=2048, zerotype="peaks"):
	if debug is True:
		print "defocus %.2f microns (underfocus is positive)"%(focus*1e6)
		print "pixelsize %.3f Angstroms"%(pixelsize*1e10)
		print "C_s %.1f mm"%(cs*1e3)
		print "High tension %.1f kV"%(volts*1e-3)
	if focus*1e6 > 15.0 or focus*1e6 < 0.1:
		apDisplay.printWarning("atypical defocus value %.1f microns (underfocus is positive)"
			%(focus*1e6))
	if cs*1e3 > 4.0 or cs*1e3 < 0.4:
		apDisplay.printWarning("atypical C_s value %.1f mm"%(cs*1e3))
	if pixelsize*1e10 > 20.0 or pixelsize*1e10 < 0.1:
		apDisplay.printWarning("atypical pixel size value %.1f Angstroms"%(pixelsize*1e10))
	if volts*1e-3 > 400.0 or volts*1e-3 < 60:
		apDisplay.printWarning("atypical high tension value %.1f kiloVolts"%(volts*1e-3))

	xfreq = 1.0/( (cols-1)*2.*pixelsize )
	xorigin = cols/2. - 0.5
	wavelength = getTEMLambda(volts)

	a = 0.5*cs*math.pi*wavelength**3
	b = -focus*math.pi*wavelength
	c = -math.asin(ampconst)
	if debug is True:
		print "quadradtic parameters %.3e, %.3e, %.3e"%(a,b,c)
	#eq: sin^2 (a r^4 + b r^2 + c) = 0
	#==> a r^4 + b r^2 + c - n*pi/2 = 0
	#quadradtic: r^2 = [ -b +/- sqrt( b^2 - 4*a*(c + n*pi/2)) ] / 2*a
	# note: "-b + sqrt(..)" is always the positive (non-imaginary) root 

	## after a certain point the peaks switch direction
	#peakswitch = (2.0*math.sqrt(focus/(cs*wavelength**2)))/math.pi + 0.9
	#if debug is True:
	#	print "Peak switch", peakswitch

	distances = []
	for i in range(numzeros):
		if zerotype.startswith("valley"):	
			innerroot = b**2. - 4. * a * (c + (i+1)*math.pi)	## just valleys/minima
		elif zerotype.startswith("peak"):
			innerroot = b**2. - 4. * a * (c + (i+0.5)*math.pi)	## just peaks/maxima
		else:
			innerroot = b**2. - 4. * a * (c + (i/2.0+0.5)*math.pi)	## all extrema
		if innerroot < 0:
			continue
		root = math.sqrt(innerroot)
		radsq1 = (-b + root)/(2*a)
		radsq2 = (-b - root)/(2*a)
		if radsq1 > 0 and radsq1 < radsq2:
			rad1 = math.sqrt(radsq1)
			pixeldist = rad1/xfreq
		elif radsq2 > 0 and radsq2 < radsq1:
			rad2 = math.sqrt(radsq2)
			pixeldist = rad2/xfreq
		else:
			print "ERROR"
		distances.append(pixeldist)
		if debug is True:
			print "radius of zero number %d is %d pixels"%(i+1, pixeldist)
	return distances


#===================
def getFirstCTFzeroRadius(focus=-1.0e-6, pixelsize=1.0e-10, cs=2e-2, 
		volts=120000, ampconst=0.000, cols=2048):
	if debug is True:
		print "defocus %.2f microns"%(focus*1e6)
		print "pixelsize %.3f Angstroms"%(pixelsize*1e10)
		print "C_s %.1f mm"%(cs*1e2)
		print "High tension %.1f kV"%(volts*1e-3)

	xfreq = 1.0/( (cols-1)*2.*pixelsize )
	xorigin = cols/2. - 0.5

	wavelength = getTEMLambda(volts)

	a = 0.5*cs*math.pi*wavelength**3
	b = focus*math.pi*wavelength
	c = -math.asin(ampconst)
	if debug is True:
		print "quadradtic parameters %.3e, %.3e, %.3e"%(a,b,c)
	#eq: sin (a r^4 + b r^2 + c) = 0
	#==> a r^4 + b r^2 + c = n*pi
	#quadradtic: r^2 = [ -b +/- sqrt( b^2 - 4*a*(c-n*pi)) ] / 2*a
	# note: "-b + sqrt(..)" is always the positive (non-imaginary) root 

	root = math.sqrt(b**2 - 4 * a * (c + math.pi/2.0))
	radsq = (-b + root)/(2*a)
	print (-b + root)/(2*a), (-b - root)/(2*a)
	rad = math.sqrt(radsq)
	pixeldist = rad/xfreq
	if debug is True:
		print "radius of first zero is %d pixels"%(pixeldist)
	return pixeldist

#===================
def getTEMLambda(volts):
	"""
	get the relativistic wavelength of the electrons in meters from volts (not kilovolts)

	see http://en.wikipedia.org/wiki/Electron_diffraction#Wavelength_of_electrons
	"""
	#f64 planck = 6.6260709544e-34;
	#f64 e_mass = 9.10938188e-31;
	#f64 e_charge = 1.60217646e-19;
	#f64 c_speed = 299792458.0;
	
	t1 = 1.2265191e-9  # This is planck/sqrt(2*e_masss*e_charge)
	t2 = 9.7840893e-7  # This is e_charge/(2*e_mass*c_speed*c_speed)

	wavelength = t1/math.sqrt(volts + t2 * volts**2);
	
	if debug is True:
		print "wavelength %.4f Angstroms"%(wavelength*1e10)

	return wavelength

#============
def getPowerSpectraPreBin(outerresolution, apix):
	if debug is True:
		print "Resolution request   %.3f"%(outerresolution)
		print "Init max resolution  %.3f"%(apix*2)
	powertwo = math.log(outerresolution/apix)/math.log(2.0)-1
	prebin = int(2**math.floor(powertwo))
	if prebin < 1:
		prebin = 1
	if debug is True:
		print "Pre-Binning", prebin
		print "Final max resolution %.3f"%(apix*prebin*2)
	return prebin

#============
def powerSpectraToOuterResolution(image, outerresolution, apix):
	"""
	apix and outerresolution must have same units (e.g., Anstroms or meters)
	"""
	if debug is True:
		print "Computing power spectra..."
	data = imagefun.power(image, mask_radius=1)
	#data = numpy.exp(data)
	powerspec, trimapix = trimPowerSpectraToOuterResolution(data, outerresolution, apix)
	return powerspec, trimapix

#============
def trimPowerSpectraToOuterResolution(powerspec, outerresolution, apix):
	"""
	apix and outerresolution must have same units (e.g., Anstroms or meters)

		resolution = (# columns) * apix / (pixel distance from center)
	therefore:
		pixel distance from center = (# columns) * apix / resolution
	"""
	if debug is True:
		print "trimPowerSpectraToOuterResolution()"
	#initresolution = apix*2
	freq = 1./(apix*powerspec.shape[0])
	initresolution = apix * 2
	if debug is True:
		print "__Pixel size", apix
		print "__Image shape   %d x %d"%(powerspec.shape[0], powerspec.shape[1])
		print "__Frequeny   %.3e"%(freq)
		print "__Resolution request   %.3f"%(outerresolution)
		print "__Init max resolution  %.3f"%(initresolution)
	if initresolution > outerresolution:
		apDisplay.printError("Requested resolution (%.3f) is not available (%.3f)"
			%(outerresolution, initresolution))
	#pixrad = # of pixels from center
	#res = [imagewidth*apix]/pixrad = 1/(freq * pixrad)
	# ==> pixrad = 1/(freq*res)
	pixellimitradius = int(math.ceil(1./(freq * outerresolution)))
	goodpixellimitradius = apPrimeFactor.getNextEvenPrime(pixellimitradius)
	finalres = 1./(freq * goodpixellimitradius)
	if debug is True:
		print "__Pixel limit dimension: ", goodpixellimitradius
		print "__Final max resolution %.3f"%(finalres)
	### convert to diameter and trim
	newshape = (goodpixellimitradius*2, goodpixellimitradius*2)
	if debug is True:
		print "__Trimming image"	
	trimpowerspec = imagefilter.frame_cut(powerspec, newshape)
	if newshape != trimpowerspec.shape:
		apDisplay.printError("shape mismatch for frame_cut (%d,%d) --> (%d,%d) = (%d,%d)"
			%(powerspec.shape[0],powerspec.shape[1],
			newshape[0],newshape[1],
			trimpowerspec.shape[0],trimpowerspec.shape[1]))
	if debug is True:
		print "original image size %d x %d"%(powerspec.shape)
		print "trimmed  image size %d x %d"%(trimpowerspec.shape)
	trimapix = apix * powerspec.shape[0] / float(trimpowerspec.shape[0])
	if debug is True:
		print "original pixel size %.3f"%(apix)
		print "trimmed  pixel size %.3f"%(trimapix)
	trimfreq = powerspec.shape[0]*trimapix
	return trimpowerspec, trimapix

#============
def draw_ellipse_to_file(jpgfile, imgarray, major, minor, angle, center=None, 
		numpoints=64, color="#3d3df2", width=4):
	"""
	major - major axis radius (in pixels)
	minor - minor axis radius (in pixels)
	angle - angle (in degrees)
	center - position of centre of ellipse
	numpoints - # of points used that make an ellipse
	"""
	if center is None:
		center = numpy.array(imgarray.shape, dtype=numpy.float)/2.0

	points = ellipse.generate_ellipse(major, minor, angle, center, numpoints, None, "step", True)
	x = points[:,0]
	y = points[:,1]

	## wrap around to end
	x = numpy.hstack((x, [x[0],]))
	y = numpy.hstack((y, [y[0],]))
	## convert image
	originalimage = imagefile.arrayToImage(imgarray)
	originalimage = originalimage.convert("RGB")
	pilimage = originalimage.copy()
	draw = ImageDraw.Draw(pilimage)
	for i in range(len(x)-1):
		xy = (x[i], y[i], x[i+1], y[i+1])
		draw.line(xy, fill=color, width=width)

	## create an alpha blend effect
	originalimage = Image.blend(originalimage, pilimage, 0.9)
	originalimage.save(jpgfile, "JPEG", quality=85)
	return

#============
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
		outercutsize = (shape[0]/2-2)/ringwidth
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
	xdata = numpy.array(xdataint, dtype=numpy.float32)*ringwidth

	if debug is True:
		print "... finish rotational average"
		apDisplay.printMsg("  expected size of rotational average: %d"%(image.shape[0]/2))
		apDisplay.printMsg("actual max size of rotational average: %d"%(xdata.max())) 

	return xdata, ydata

#============
def ellipticalAverage(image, ellipratio, ellipangle, ringwidth=3.0, innercutradius=None, full=False, median=False, filename=None):
	"""
	compute the elliptical average of a 2D numpy array

	ellipratio: ratio of elliptical axes ( >= 1 )
				= major / minor = a / b
				= circle has a value of 1
	
	ellipangle: angle of ellipse in degrees
			
	full : False -- only average complete circles (no edges/corners)
	       True  -- rotational average out to corners of image

	median : False -- calculate the mean of each ring
	         True  -- calculate the median of each ring (slower)
	"""
	if ellipratio < 1:
		ellipratio = 1.0/ellipratio
		ellipangle += 90
	while ellipangle > 180:
		ellipangle -= 180
	while ellipangle < 0:
		ellipangle += 180

	if debug is True:
		apDisplay.printColor("ellipangle = %.3f (file = %s)"%(ellipangle, filename), "cyan")

	if debug is True:
		print "ring width %.2f pixels"%(ringwidth)

	shape = numpy.array(numpy.array(image.shape)*math.sqrt(2)/2., dtype=numpy.int)*2
	if debug is True:
		print "new shape", shape
	## create a grid of distance from the center
	xhalfshape = shape[0]/2.0
	x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
	yhalfshape = shape[1]/2.0
	y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
	xx, yy = numpy.meshgrid(x, y)
	### apply ellipse ratio
	yy = ellipratio*yy
	radial = xx**2 + yy**2
	### apply ellipse rotation
	#imagefile.arrayToPng(numpy.array(radial, dtype=numpy.float32), filename+"radial-norot.png")
	radial = scipy.ndimage.interpolation.rotate(radial, angle=ellipangle, 
		reshape=False, mode='wrap', order=2)
	#imagefile.arrayToPng(numpy.array(radial, dtype=numpy.float32), filename+"radial-uncut.png")
	radial = imagefilter.frame_cut(radial, image.shape)
	if debug is True:
		print "minimal radial distance", radial.min()
	radial = numpy.sqrt(radial)

	#imagefile.arrayToPng(image, filename+"image.png")
	
	## convert to integers
	radial = radial/ringwidth
	radial = numpy.array(radial, dtype=numpy.int32)
	#imagefile.arrayToPng(numpy.array(radial, dtype=numpy.float32), filename+"radial.png")
	if shape[0] < 32:
		print radial

	count = 0
	if debug is True:
		print "computing elliptical average xdata..."
	xdataint = numpy.unique(radial)

	if full is False:
		### trims any edge artifacts from rotational average
		if debug is True:
			print "ellipratio", ellipratio
		outercutsize = (shape[0]/2-2)/ringwidth*math.sqrt(2)/2.
		if debug is True:
			apDisplay.printColor("Num X points %d, Half image size %d, Outer cut size %d, Ringwidth %.2f, Percent trim %.1f"
				%(xdataint.shape[0], shape[0]/2-2, outercutsize, ringwidth, 100.*outercutsize/float(xdataint.shape[0])), "yellow")
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
		print "computing elliptical average ydata..."
	ydata = numpy.array(scipy.ndimage.mean(data, radial, xdataint))
	### WHAT ARE YOU DOING WITH THE SQRT ellipratio???
	xdata = numpy.array(xdataint, dtype=numpy.float32)*ringwidth/math.sqrt(ellipratio)

	if debug is True:
		print "... finish elliptical average"
		apDisplay.printMsg("  expected size of elliptical average: %d"%(image.shape[0]/2))
		apDisplay.printMsg("actual max size of elliptical average: %d"%(xdata.max())) 


	return xdata, ydata
