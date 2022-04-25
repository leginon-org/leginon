
## pythonlib
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

#=========================
def binImg(imgarray, bin=1, warn=True):
	"""
	returns a binned image of a 2D image
	"""
	if bin <= 1:
		return imgarray
	oldshape = numpy.asarray(imgarray.shape)
	bin2 = bin * 2
	remain = oldshape % bin2
	if remain.any():
		maxx = int(oldshape[0]/bin2)*bin2
		maxy = int(oldshape[1]/bin2)*bin2
		cutshape = numpy.asarray((maxx, maxy))
		if warn is True:
			apDisplay.printWarning("rescaling array to fit bin dimensions: "+str(oldshape)+" -> "+str(cutshape))
		imgarray = frame_cut(imgarray, cutshape)
		newshape = numpy.asarray(cutshape)/bin
	else:
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
def pixelLimitFilter(imgarray, pixlimit=0, const=False, msg=True):
	if pixlimit < 0.1:
		return imgarray
	mean1 = imgarray.mean()
	std1 = imgarray.std()
	upperbound = mean1 + pixlimit * std1
	lowerbound = mean1 - pixlimit * std1
	if msg is True:
		print ".. Pixel Limits %.3f <> %.3f"%(lowerbound, upperbound)
	imgarray2 = numpy.asarray(imgarray).copy()
	if const is True:
		## replace noisy peak with new normally distributed values		
		upperreplace = numpy.ones(imgarray2.shape)*upperbound
		lowerreplace = numpy.ones(imgarray2.shape)*lowerbound
	else:
		## replace noisy peak with new normally distributed values
		normalreplace = numpy.random.normal(mean1, std1/1.5, (imgarray2.shape))
		## double check still in range
		if normalreplace.max() > upperbound:
			normalreplace = numpy.where(normalreplace > upperbound, upperbound, normalreplace)
		if normalreplace.min() < lowerbound:
			normalreplace = numpy.where(normalreplace < lowerbound, lowerbound, normalreplace)
		upperreplace = normalreplace
		lowerreplace = normalreplace
	## replace noisy peak with new values
	if msg is True:
		total = imgarray2.shape[0]*imgarray2.shape[1]
		repl = numpy.where(imgarray2 > upperbound, 1, 0).sum()
		repl += numpy.where(imgarray2 < lowerbound, 1, 0).sum()
		if repl > 0:
			apDisplay.printMsg(".. replacing %d of %d pixels with pixel limit"%(repl, total))
	imgarray2 = numpy.where(imgarray2 > upperbound, upperreplace, imgarray2)
	imgarray2 = numpy.where(imgarray2 < lowerbound, lowerreplace, imgarray2)
	return imgarray2.copy()

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
def subtractHighPassFilter(imgarray, apix=1.0, bin=1, radius=0.0, localbin=8, msg=True):
	"""
	high pass filter image to radius resolution, using stupid Gaussian filter
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
	#cs_center = cs_shape[0]/2, cs_shape[1]/2 #this is never used
	circ = _gradient(cs_shape,zero_radius)
	center_square[:] = center_square * circ.astype(center_square.dtype)

#=========================
def planeRegression(imgarray, msg=True):
	"""
	performs a two-dimensional linear regression and subtracts it from an image
	essentially a fast high pass filter
	z' = a*x + b*y + c
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
	#zsumsq = (imgarray*imgarray).sum()

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
def parabolicRegression(imgarray, msg=True):
	"""
	performs a two-dimensional linear regression and subtracts it from an image
	essentially a fast high pass filter
	z' = a*x^2 + b*x*y + c*y^2 + d*x + e*y + f
	"""
	raise NotImplementedError

#=========================
def scaleImage(imgdata, scale):
	"""
	scale an image
	"""
	if scale == 1.0:
		return imgdata
	if min(imgdata.shape) * scale < 2:
		apDisplay.printError("Image would be scaled to less than 2 pixels in length, aborted")
	return ndimage.zoom(imgdata, scale, order=1)


#=========================
def frame_cut(a, newshape):
	"""
	clips image, similar to EMAN1's proc2d clip=X,Y
	
	>>> a = num.arange(16, shape=(4,4))
	>>> frame_cut(a, (2,2))
	array(
			[[5,  6],
		   [9, 10]])
	"""
	mindimx = int( (a.shape[0] / 2.0) - (newshape[0] / 2.0) )
	maxdimx = int( (a.shape[0] / 2.0) + (newshape[0] / 2.0) )
	mindimy = int( (a.shape[1] / 2.0) - (newshape[1] / 2.0) )
	maxdimy = int( (a.shape[1] / 2.0) + (newshape[1] / 2.0) )
	#print mindimx, maxdimx, mindimy, maxdimy
	return a[mindimx:maxdimx, mindimy:maxdimy]

#=========================
def frame_constant(a, shape, cval=0):
	"""
	frame_constant creates an oversized copy of 'a' with new 'shape'
	and the contents of 'a' in the center.  The boundary pixels are
	constant.

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

#=========================
def tanhHighPassFilter(data, radius, apix=1.0, bin=1):
	"""
	performs a hyperbolic tangent high pass filter 
	in python using only numpy libraries that is
	designed to be similar to EMAN1 proc2d
	
	Note: radius is in real space units
	"""
	pixelradius = radius/apix/float(bin)
	if pixelradius < 1:
		apDisplay.printWarning("pixel radius too small for high pass filter")
		return data		
	filter = tanhFilter(pixelradius, data.shape, fuzzyEdge=2)
	fftdata = ffteng.transform(data)
	fftdata = numpy.fft.fftshift(fftdata)
	fftdata *= filter
	fftdata = numpy.fft.fftshift(fftdata)
	flipdata = numpy.real(numpy.fft.ifft2(fftdata))
	return flipdata

#=========================
def tanhLowPassFilter(data, radius, apix=1.0, bin=1):
	"""
	performs a hyperbolic tangent high pass filter 
	in python using only numpy libraries that is
	designed to be similar to EMAN1 proc2d
	
	Note: radius is in real space units
	"""
	pixelradius = radius/apix/float(bin)
	if pixelradius < 1:
		apDisplay.printWarning("pixel radius too small for low pass filter")
		return data	
	#opposite of HP filter
	filter = 1.0 - tanhFilter(pixelradius, data.shape, fuzzyEdge=2)
	fftdata = ffteng.transform(data)
	fftdata = numpy.fft.fftshift(fftdata)
	fftdata *= filter
	fftdata = numpy.fft.fftshift(fftdata)
	flipdata = numpy.real(numpy.fft.ifft2(fftdata))
	return flipdata

filterCache = {}

#=========================
def tanhFilter(pixelradius, shape, fuzzyEdge=2):
	"""
	creates hyperbolic tangent mask of size pixelradius
	into a numpy array of defined shape

	fuzzyEdge makes the edge of the hyperbolic tangent more fuzzy
	"""
	filterKey = "%.3f-%d-%.3f"%(pixelradius, max(shape), fuzzyEdge)
	try:
		return filterCache[filterKey]
	except KeyError:
		pass
	xhalfshape = shape[0]/2.0
	x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
	yhalfshape = shape[1]/2.0
	y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
	yy, xx = numpy.meshgrid(y, x)
	radial = xx**2 + yy**2 #- 0.5
	radial = numpy.sqrt(radial)
	filter = numpy.tanh(radial/fuzzyEdge - 1.01*(max(shape))/float(pixelradius)/fuzzyEdge)/2.0 + 0.5
	filterCache[filterKey] = filter
	return filter

####
# This is a low-level file with NO database connections
# Please keep it this way
####
