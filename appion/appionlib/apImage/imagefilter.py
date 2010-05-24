#Part of the new pyappion

## pythonlib
import os
import time
## numpy
import numpy
import pyami.quietscipy
from scipy import ndimage
from numpy import linalg
## appion
from appionlib import apDisplay
from appionlib.apSpider import filters
## pyami
from pyami import imagefun, fftengine

ffteng = fftengine.fftEngine()

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#=========================
def _processImage(imgarray, bin=1, apix=1.0, lowpass=0.0, highpass=0.0,
		planeReg=True, median=0, invert=False, pixlimit=0, msg=True):
	"""
	standard processing for an image
	"""
	simgarray = imgarray.copy()
	if median > 0:
		simgarray = ndimage.median_filter(simgarray, size=median)
	simgarray = binImg(simgarray, bin)
	if planeReg is True:
		simgarray = planeRegression(simgarray, msg)
	#simgarray = highPassFilter(simgarray, apix, bin, highpass, msg=msg)
	simgarray = fermiHighPassFilter(simgarray, apix, bin, highpass, msg=msg)
	simgarray = pixelLimitFilter(simgarray, pixlimit)
	simgarray = lowPassFilter(simgarray, apix, bin, lowpass, msg)
	#simgarray = fermiLowPassFilter(simgarray, apix, bin, lowpass, msg)
	if invert is True:
		simgarray = invertImage(simgarray)
	simgarray = 255.0*(normRange(simgarray)+1.0e-7)
	return simgarray

#=========================
def preProcessImage(imgarray, bin=None, apix=None, lowpass=None, planeReg=None,
		median=None, highpass=None, correct=False, invert=None, pixlimit=None, msg=None,
		params={}):
	"""
	standard processing for an image
	"""
	startt = time.time()
	#MESSAGING
	if msg is None:
		if 'background' in params:
			msg = not params['background']
		else:
			msg = True
	#BINNING
	if bin is None:
		if 'bin' in params:
			bin = params['bin']
		else:
			bin = 1
	#PLANE REGRESSION
	if planeReg is None:
		if 'planereg' in params:
			planeReg = params['planereg']
		else:
			planeReg = False
	#ANGSTROMS PER PIXEL
	if apix is None:
		if 'apix' in params:
			apix = params['apix']
		else:
			apDisplay.printError("'apix' is not defined in preProcessImage()")
	#MEDIAN FILTER
	if median is None:
		if 'median' in params:
			median = params['median']
		else:
			median = 0
	#LOW PASS FILTER
	if lowpass is None:
		if 'lowpass' in params and params['lowpass'] is not None:
			lowpass = params['lowpass']
		elif 'lp' in params and params['lp'] is not None:
			lowpass = params['lp']
		else:
			lowpass = 0
	#INVERT IMAGE
	if invert is None:
		if 'invert' in params:
			invert = params['invert']
		else:
			invert = False
			apDisplay.printWarning("'invert' is not defined in preProcessImage()")
	#HIGH PASS FILTER
	if highpass is None:
		if 'highpass' in params:
			highpass = params['highpass']
		elif 'hp' in params:
			highpass = params['hp']
		else:
			highpass = 0
	#PIXEL LIMITATION FILTER
	if pixlimit is None:
		if 'pixlimit' in params:
			pixlimit = params['pixlimit']
		else:
			pixlimit = 0
	#HIGH PASS FILTER => PLANE REGRESSION
	result = _processImage(imgarray, bin, apix, lowpass, highpass, planeReg, median, invert, pixlimit, msg)
	if msg is True:
		apDisplay.printMsg("filtered image in "+apDisplay.timeString(time.time()-startt))
	return result

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
def binImg(imgarray, bin=1, warn=True):
	"""
	returns a binned image of a 2D image
	"""
	if bin <= 1:
		return imgarray
	oldshape = numpy.asarray(imgarray.shape)
	remain = oldshape % bin
	if remain.any():
		maxx = int(oldshape[0]/bin)*bin
		maxy = int(oldshape[1]/bin)*bin
		cutshape = numpy.asarray((maxx, maxy))
		if warn is True:
			apDisplay.printWarning("rescaling array to fit bin dimensions: "+str(oldshape)+" -> "+str(cutshape))
		imgarray = frame_cut(imgarray, cutshape)
	newshape = numpy.asarray(oldshape)/bin
	tmpshape = (newshape[0], bin, newshape[1], bin)
	f = bin * bin
	binned = numpy.sum(numpy.sum(numpy.reshape(imgarray, tmpshape), 1), 2) / f
	return binned

#=========================
def invertImage(imgarray):
	"""
	returns a contrast inverted image
	"""
	return -1.0*imgarray

#=========================
def filterImg(imgarray,apix=1.0,rad=0.0,bin=1):
	#TEMPORARY ALIAS FOR lowPassFilter
	return lowPassFilter(imgarray,apix=apix,bin=1,radius=rad)

#=========================
def pixelLimitFilter(imgarray, pixlimit=0):
	if pixlimit < 0.1:
		return imgarray
	mean1 = imgarray.mean()
	std1 = imgarray.std()
	upperbound = mean1 + pixlimit * std1
	lowerbound = mean1 - pixlimit * std1
#	print mean1,std1
	imgarray2 = numpy.asarray(imgarray)
#	print imgarray2
	imgarray2 = numpy.where(imgarray2 > upperbound, upperbound, imgarray2)
	imgarray2 = numpy.where(imgarray2 < lowerbound, lowerbound, imgarray2)
#	print imgarray2
	return imgarray2

#=========================
def lowPassFilter(imgarray, apix=1.0, bin=1, radius=0.0, msg=True):
	"""
	low pass filter image to radius resolution
	"""
	if radius is None or radius == 0:
		if msg is True:
			apDisplay.printMsg("skipping low pass filter")
		return(imgarray)
	sigma=float(radius/apix/float(bin))
	return ndimage.gaussian_filter(imgarray, sigma=sigma/3.0)

#=========================
def fermiHighPassFilter(imgarray, apix=1.0, bin=1, radius=0.0, msg=True):
	"""
	Fermi high pass filter image to radius resolution
	"""
	if radius is None or radius == 0:
		if msg is True:
			apDisplay.printMsg("skipping high pass filter")
		return(imgarray)
	pixrad = float(radius/apix/float(bin))
	filtimg = filters.fermiHighPassFilter(imgarray, pixrad)
	return filtimg

#=========================
def fermiLowPassFilter(imgarray, apix=1.0, bin=1, radius=0.0, msg=True):
	"""
	Fermi low pass filter image to radius resolution
	"""
	if radius is None or radius == 0:
		if msg is True:
			apDisplay.printMsg("skipping low pass filter")
		return imgarray
	pixrad = float(radius/apix/float(bin))
	if pixrad < 2.0:
		apDisplay.printWarning("low pass filter radius "+str(round(pixrad,2))+" is less than 2 pixels; skipping filter")
		return imgarray
	filtimg = filters.fermiLowPassFilter(imgarray, pixrad)
	return filtimg

#=========================
def highPassFilter(imgarray, apix=1.0, bin=1, radius=0.0, localbin=8, msg=True):
	"""
	high pass filter image to radius resolution
	"""
	if radius is None or radius < 1 or imgarray.shape[0] < 256:
		if msg is True:
			apDisplay.printMsg("skipping high pass filter")
		return(imgarray)
	try:
		bimgarray = binImg(imgarray, localbin)
		sigma=float(radius/apix/float(bin*localbin))
		filtimg = ndimage.gaussian_filter(bimgarray, sigma=sigma)
		expandimg = scaleImage(filtimg, localbin)
		expandimg = frame_constant(expandimg, imgarray.shape)
		filtimg = imgarray - expandimg
	except:
		apDisplay.printWarning("High Pass Filter failed")
		return imgarray
	return filtimg

#=========================
def maskHighPassFilter(imgarray, apix=1.0, bin=1, zero_res=0.0, one_res=0.0, msg=True):
	"""
	high pass filter that ensures the fft values within zero_radius is zero to avoid
	interference of really strong structure factors, only works right for square image
	"""
	if one_res is None or one_res < 1 or zero_res < 1 or imgarray.shape[0] < 256:
		if msg is True:
			apDisplay.printMsg("skipping high pass filter")
		return(imgarray)
	shape = imgarray.shape
	zero_radius = apix*min(shape)/zero_res/bin
	one_radius = apix*min(shape)/one_res/bin
	print zero_radius, one_radius
	try:
		filtimg = _maskHighPassFilter(imgarray,zero_radius, one_radius)
	except:
		raise
		apDisplay.printWarning("Mask High Pass Filter failed")
		return imgarray
	return filtimg

#=========================
def _maskHighPassFilter(a,zero_radius,one_radius):
	if zero_radius == 0 or zero_radius > one_radius:
		return a
	fft = ffteng.transform(a)
	fft = imagefun.swap_quadrants(fft)
	_center_mask(fft,zero_radius,one_radius)
	bfft = imagefun.swap_quadrants(fft)
	b = ffteng.itransform(bfft)
	return b

#=========================
def _gradient(cs_shape,zeroradius):
	oneradius = min(cs_shape[0]/2.0,cs_shape[1]/2.0)
	a = numpy.indices(cs_shape)
	cut = zeroradius/float(oneradius)
	radii = numpy.hypot(a[0,:]-(cs_shape[0]/2.0-0.5),a[1,:]-(cs_shape[1]/2.0-0.5))/oneradius	
	def _grad(r):
		return (r-cut)/(1-cut)
	g = numpy.piecewise(radii,[radii < cut,numpy.logical_and(radii < 1, radii >=cut),
         radii>=1-cut],[0,_grad,1])
	return g

#=========================
def _center_mask(a, zero_radius,one_radius):
	shape = a.shape
	center = shape[0]/2, shape[1]/2
	center_square = a[center[0]-one_radius:center[0]+one_radius, center[1]-one_radius:center[1]+one_radius]
	cs_shape = center_square.shape
	cs_center = cs_shape[0]/2, cs_shape[1]/2
	circ = _gradient(cs_shape,zero_radius)
	center_square[:] = center_square * circ.astype(center_square.dtype)

#=========================
def planeRegression(imgarray, msg=True):
	"""
	performs a two-dimensional linear regression and subtracts it from an image
	essentially a fast high pass filter
	"""


	### create index arrays, e.g., [1, 2, 3, 4, 5, ..., N]
	def retx(y,x):
		return x
	def rety(y,x):
		return y
	xarray = numpy.fromfunction(retx, imgarray.shape, dtype=numpy.float32)
	yarray = numpy.fromfunction(rety, imgarray.shape, dtype=numpy.float32)
	xsize = imgarray.shape[0]
	ysize = imgarray.shape[1]
	xarray = xarray/(ysize-1.0) - 0.5
	yarray = yarray/(xsize-1.0) - 0.5

	### get running sums
	count =  float(xsize*ysize)
	xsum =   xarray.sum()
	xsumsq = (xarray*xarray).sum()
	ysum =   yarray.sum()
	ysumsq = (yarray*yarray).sum()
	xysum =  (xarray*yarray).sum()
	xzsum =  (xarray*imgarray).sum()
	yzsum =  (yarray*imgarray).sum()
	zsum =   imgarray.sum()
	zsumsq = (imgarray*imgarray).sum()

	### create linear algebra matrices
	leftmat = numpy.array( [[xsumsq, xysum, xsum], [xysum, ysumsq, ysum], [xsum, ysum, count]], dtype=numpy.float64)
	rightmat = numpy.array( [xzsum, yzsum, zsum], dtype=numpy.float64)

	### solve eigen vectors
	resvec = linalg.solve(leftmat,rightmat)

	### show solution
	if msg is True:
		apDisplay.printMsg("plane_regress: x-slope: %.3f, y-slope: %.3f, xy-intercept: %.3f"
			%(resvec[0], resvec[1], resvec[2]))

	### subtract plane from array
	newarray = imgarray - xarray*resvec[0] - yarray*resvec[1] - resvec[2]
	return newarray

#=========================
def scaleImage(imgdata, scale):
	"""
	scale an image
	"""
	if scale == 1.0:
		return imgdata
	return ndimage.zoom(imgdata, scale, order=1)

#=========================
def correctImage(imgdata, sessionname):
	"""
	Correct an image using the old method:
	- no bias correction
	- dark correction is not time dependent
	"""
	rawimgarray = imgdata['image']
	from appionlib import apDatabase
	darkarray, normarray = apDatabase.getDarkNorm(sessionname, imgdata['camera'])
	correctedimgarray = normarray * (rawimgarray - darkarray)
	return correctedimgarray

#=========================
def frame_cut(a, newshape):
	mindimx = int( (a.shape[0] / 2.0) - (newshape[0] / 2.0) )
	maxdimx = int( (a.shape[0] / 2.0) + (newshape[0] / 2.0) )
	mindimy = int( (a.shape[1] / 2.0) - (newshape[1] / 2.0) )
	maxdimy = int( (a.shape[1] / 2.0) + (newshape[1] / 2.0) )
	return a[mindimx:maxdimx, mindimy:maxdimy]

#=========================
def frame_constant(a, shape, cval=0):
	"""
	frame_nearest creates an oversized copy of 'a' with new 'shape'
	and the contents of 'a' in the center.  The boundary pixels are
	copied from the nearest edge pixel in 'a'.

	>>> a = num.arange(16, shape=(4,4))
	>>> frame_constant(a, (8,8), cval=42)
	array(
			[[42, 42, 42, 42, 42, 42, 42, 42],
		   [42, 42, 42, 42, 42, 42, 42, 42],
		   [42, 42,  0,  1,  2,  3, 42, 42],
		   [42, 42,  4,  5,  6,  7, 42, 42],
		   [42, 42,  8,  9, 10, 11, 42, 42],
		   [42, 42, 12, 13, 14, 15, 42, 42],
		   [42, 42, 42, 42, 42, 42, 42, 42],
		   [42, 42, 42, 42, 42, 42, 42, 42]])

	"""

	b = numpy.zeros(shape, dtype=a.dtype)
	delta = (numpy.array(b.shape) - numpy.array(a.shape))
	dy = delta[0] // 2
	dx = delta[1] // 2
	my = a.shape[0] + dy
	mx = a.shape[1] + dx

	b[dy:my, dx:mx] = a			 # center
	b[:dy,dx:mx]  = cval			 # top
	b[my:,dx:mx]  = cval			 # bottom
	b[dy:my, :dx] = cval			 # left
	b[dy:my, mx:] = cval			 # right
	b[:dy, :dx]   = cval			 # topleft
	b[:dy, mx:]   = cval			 # topright
	b[my:, :dx]   = cval			 # bottomleft
	b[my:, mx:]   = cval			 # bottomright
	return b

#=========================
def spiderTransform(a, rot=0, shift=(0,0), mirror=False, order=2):
	"""
	rotates (in degrees) about an off-center pixel, then shifts (in pixels) and last mirrors an array

	FROM http://www.wadsworth.org/spider_doc/spider/docs/man/apmq.html

	UNTESTED
	"""
	### make a copy
	b = a

	### rotate is positive, but shifted by a half pixel
	b = ndimage.shift(b, shift=(-0.5, -0.5), mode='wrap', order=order)
	b = ndimage.rotate(b, angle=rot, reshape=False, mode='reflect', order=order)
	b = ndimage.shift(b, shift=(0.5, 0.5), mode='wrap', order=order)

	# shift is in rows/columns not x,y
	rowcol = (shift[1],shift[0])
	b = ndimage.shift(b, shift=rowcol, mode='reflect', order=order)

	# mirror the image about the y-axis, i.e. flip left-right
	if mirror is True:
		b = numpy.fliplr(b)

	return b


#=========================
def xmippTransform(a, rot=0, shift=(0,0), mirror=False, order=2):
	"""
	shift, mirror, then rotate (in degrees) about an off-center pixel
	rotates (in degrees) then shifts (in pixels) then mirrors an array, just like SPIDER

	FROM http://xmipp.cnb.uam.es/twiki/bin/view/Xmipp/AlignementParametersNote
	"""
	### make a copy
	b = a

	### shift is in rows/columns not x,y
	rowcol = (shift[1],shift[0])
	b = ndimage.shift(b, shift=rowcol, mode='reflect', order=order)

	### mirror the image about the y-axis, i.e. flip left-right
	if mirror is True:
		b = numpy.fliplr(b)
	
	### rotate is positive, but shifted by a half pixel
	b = ndimage.shift(b, shift=(-0.5, -0.5), mode='wrap', order=order)
	b = ndimage.rotate(b, angle=-1*rot, reshape=False, mode='reflect', order=order)
	b = ndimage.shift(b, shift=(0.5, 0.5), mode='wrap', order=order)

	return b

####
# This is a low-level file with NO database connections
# Please keep it this way
####
