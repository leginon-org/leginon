#Part of the new pyappion

#pythonlib
import math
import time
#PIL
import Image
import ImageDraw
#numpy
import numpy
from scipy import ndimage
from numpy import linalg
from numpy import ma
#pyami
import apDisplay
try:
	from pyami import mrc
	from pyami import imagefun
	from pyami import convolver
	import leginondata
except:
	apDisplay.printError("pymai is required, type 'usepythoncvs'")
#appion

import apDB

db=apDB.db

def _processImage(imgarray, bin=1, apix=1.0, lowpass=0.0, highpass=0.0, planeReg=True, median=0, invert=False):
	"""
	standard processing for an image
	"""
	simgarray = imgarray.copy()
	simgarray = binImg(simgarray,bin)
	if median > 0:
		simgarray = ndimage.median_filter(simgarray, size=median)
	simgarray = lowPassFilter(simgarray,apix,bin,lowpass)
	simgarray = highPassFilter(simgarray,apix,bin,highpass)
	if planeReg is True:
		simgarray = planeRegression(simgarray)
	if invert is True:
		simgarray = invertImage(simgarray)
	simgarray = 255.0*(normRange(simgarray)+1.0e-7)
	return simgarray


def preProcessImage(imgarray, bin=None, apix=None, lowpass=None, planeReg=False, 
		median=None, highpass=None, correct=False, invert=None, params={}):
	"""
	standard processing for an image
	"""
	startt = time.time()
	#BINNING
	if bin is None:
		if 'bin' in params:
			bin = params['bin']
		else:
			apDisplay.printWarning("'bin' is not defined in preProcessImage()")
			bin = 1
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
			apDisplay.printWarning("'median' is not defined in preProcessImage()")
	#LOW PASS FILTER
	if lowpass is None:
		if 'lowpass' in params:
			lowpass = params['lowpass']
		elif 'lp' in params:
			lowpass = params['lp']
		else:
			lowpass = 0
			apDisplay.printWarning("'lowpass' is not defined in preProcessImage()")
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
			apDisplay.printWarning("'highpass' is not defined in preProcessImage()")
	#HIGH PASS FILTER => PLANE REGRESSION
	result = _processImage(imgarray, bin, apix, lowpass, highpass, planeReg, median, invert)
	apDisplay.printMsg("filtered image in "+apDisplay.timeString(time.time()-startt))
	return result

def binImg(imgarray,bin=1):
	"""
	returns a binned image
	"""
	if bin > 1:
		newarray = imagefun.bin(imgarray, bin)
		mindim = min(newarray.shape)
		if mindim < 1:
			apDisplay.printError("problem in numextension bin, return null array")
			newarray = ndimage.median_filter(newarray, size=0)
		return newarray
	else:
		return imgarray

def invertImage(imgarray):
	"""
	returns a contrast inverted image
	"""
	return -1.0*imgarray

def filterImg(imgarray,apix=1.0,rad=0.0,bin=1):
	#TEMPORARY ALIAS FOR lowPassFilter
	return lowPassFilter(imgarray,apix=apix,bin=1,radius=rad)

def lowPassFilter(imgarray, apix=1.0, bin=1, radius=0.0):
	"""
	low pass filter image to radius resolution
	"""
	if radius == 0:
		print " ... skipping low pass filter"
		return(imgarray)
	sigma=float(radius/apix/float(bin))
	try:
		return ndimage.gaussian_filter(imgarray, sigma=sigma/3.0)
	except:
		if(sigma > 10):
			print " ... performing BIG and SLOW low pass filter"
		else:
			print " ... performing leginon low pass filter"
		kernel=convolver.gaussian_kernel(sigma/3.0)
		c=convolver.Convolver()
		return c.convolve(image=imgarray, kernel=kernel)

def highPassFilter(imgarray, apix=1.0, bin=1, radius=0.0, localbin=8):
	"""
	high pass filter image to radius resolution
	"""
	if radius == 0 or imgarray.shape[0] < 512:
		print " ... skipping high pass filter"
		return(imgarray)
	bimgarray = binImg(imgarray, localbin)
	sigma=float(radius/apix/float(bin*localbin))
	try:
		filtimg = ndimage.gaussian_filter(bimgarray, sigma=sigma)
	except:
		apDisplay.printWarning("High Pass Filter failed")
		return imgarray
	expandimg = scaleImage(filtimg,localbin)
	return imgarray - expandimg

def diffOfGaussParam(imgarray, params):
	apix = params['apix']
	bin = params['bin']
	diam = params['diam']
	k = params['kfactor']
	return diffOfGauss(imgarray, apix, bin, diam, k=k)

def diffOfGauss(imgarray, apix, bin, diam, k=1.2):
	"""
	given bin, apix and diam of particle perform a difference of Gaussian
	about the size of that particle
	k := sloppiness coefficient
	"""
	if diam == 0:
		apDisplay.printError("difference of Gaussian; radius = 0")
	pixrad = float(diam/apix/float(bin)/2.0)
	kfact = math.sqrt( (k**2 - 1.0) / (2.0 * k**2 * math.log(k)) )
	sigma1 = kfact * pixrad
	#sigma2 = k * sigma1
	sigmaD = math.sqrt(k*k-1.0)
	imgarray1 = ndimage.gaussian_filter(imgarray, sigma=sigma1)
	imgarray2 = ndimage.gaussian_filter(imgarray1, sigma=sigmaD)
	#kernel1 = convolver.gaussian_kernel(sigma1)
	#kernel2 = convolver.gaussian_kernel(sigmaD)
	#c=convolver.Convolver()
	#imgarray1 = c.convolve(image=imgarray,kernel=kernel1)
	#imgarray2 = c.convolve(image=imgarray1,kernel=kernelD)
	return imgarray2-imgarray1

def planeRegression(imgarray):
	"""
	performs a two-dimensional linear regression and subtracts it from an image
	essentially a fast high pass filter
	"""
	#print " ... calculate 2d linear regression"
	if ( (imgarray.shape)[0] != (imgarray.shape)[1] ):
		print "Array is NOT square"
		sys.exit(1)
	size = (imgarray.shape)[0]
	count = float((imgarray.shape)[0]*(imgarray.shape)[1])
	def retx(y,x):
		return x
	def rety(y,x):
		return y	
	xarray = numpy.fromfunction(retx, imgarray.shape)
	yarray = numpy.fromfunction(rety, imgarray.shape)
	xsum = float(xarray.sum())
	xsumsq = float((xarray*xarray).sum())
	ysum = xsum
	ysumsq = xsumsq
	xysum = float((xarray*yarray).sum())
	xzsum = float((xarray*imgarray).sum())
	yzsum = float((yarray*imgarray).sum())
	zsum = imgarray.sum()
	zsumsq = (imgarray*imgarray).sum()
	xarray = xarray.astype(numpy.float32)
	yarray = yarray.astype(numpy.float32)
	leftmat = numpy.array( [[xsumsq, xysum, xsum], [xysum, ysumsq, ysum], [xsum, ysum, count]] )
	rightmat = numpy.array( [xzsum, yzsum, zsum] )
	resvec = linalg.solve(leftmat,rightmat)
	print " ... plane_regress: x-slope:",round(resvec[0]*size,5),\
		", y-slope:",round(resvec[1]*size,5),", xy-intercept:",round(resvec[2],5)
	newarray = imgarray - xarray*resvec[0] - yarray*resvec[1] - resvec[2]
	del imgarray,xarray,yarray,resvec
	return newarray

def normRange(imgarray):
	"""
	normalize the range of an image between 0 and 1
	"""
	min1=ndimage.minimum(imgarray)
	max1=ndimage.maximum(imgarray)
	if min1 == max1:
		return imgarray - min1
	return (imgarray - min1)/(max1 - min1)

def normRangeMed(imgarray, size=5):
	"""
	normalize an image to mean = 0 and stddev = 1.0
	"""
	medimgarray = ndimage.median_filter(imgarray, size=size)
	min1 = ndimage.minimum(medimgarray)
	max1 = ndimage.maximum(medimgarray)
	if min1 == max1:
		return imgarray - min1
	return (imgarray - min1)/(max1 - min1)

def normStdev(imgarray):
	"""
	normalize an image to mean = 0 and stddev = 1.0
	"""
	avg1=ndimage.mean(imgarray)
	std1=ndimage.standard_deviation(imgarray)
	if std1 == 0:
		return imgarray - avg1
	return (imgarray - avg1)/std1

def normStdevMed(imgarray, size=3):
	"""
	normalize an image to mean = 0 and stddev = 1.0
	"""
	medimgarray = ndimage.median_filter(imgarray, size=size)
	avg1=ndimage.mean(medimgarray)
	std1=ndimage.standard_deviation(medimgarray)
	if std1 == 0:
		return imgarray - avg1
	return (imgarray - avg1)/std1

def normStdevMask(img,mask):
	"""
	normalize an image with mean = 0 and stddev = 1.0 only inside a mask
	"""
	n1	 = ndimage.sum(mask)
	if n1 == 0:
		return img
	sum1   = ndimage.sum(img*mask)
	sumsq1 = ndimage.sum(img*img*mask)
	avg1   = sum1/n1
	std1   = math.sqrt((sumsq1 - sum1*sum1/n1)/(n1-1))
	std2   = ndimage.standard_deviation(img)
	return (img - avg1) / std1

def scaleImage(imgdata, scale):
	"""
	scale an image
	"""
	if scale == 1.0:
		return imgdata
	return ndimage.zoom(imgdata, scale, order=1)

def meanEdgeValue(imgdata, w=0):
	"""
	get the average values for the edges of width = w pixels
	"""
	xmax = imgdata.shape[0]
	ymax = imgdata.shape[1]
	leftEdgeAvg   = ndimage.mean(imgdata[0:xmax,      0:w])
	rightEdgeAvg  = ndimage.mean(imgdata[0:xmax,      ymax-w:ymax])
	topEdgeAvg    = ndimage.mean(imgdata[0:w,         0:ymax])
	bottomEdgeAvg = ndimage.mean(imgdata[xmax-w:xmax, 0:ymax])
	edgeAvg       = (leftEdgeAvg + rightEdgeAvg + topEdgeAvg + bottomEdgeAvg)/4.0
	return edgeAvg

def centralMean(imgarray, trim=0.1):
	"""
	get the average values for the edges of trim = x percent
	"""	
	a = cutEdges(imgarray,trim=trim)
	return ndimage.mean(a)


#########################################################

def correlationCoefficient(x,y,mask=None):
	"""
	calcualate the correlation coefficient of two numpys
	"""
	if x.shape != y.shape:
		apDisplay.printError("images are not the same shape in correlation calc")
	if mask != None:
		if x.shape != mask.shape:
			apDisplay.printError("mask is not the same shape as images in correlation calc")
		tot = ndimage.sum(mask)
		if tot == 0:
			return 0.0
		x = normStdevMask(x,mask)
		y = normStdevMask(y,mask)
	else:
		tot = float(x.shape[0]*x.shape[1])
		x = normStdev(x)
		y = normStdev(y)
	z = x*y
	if mask != None:
		z = z*mask
	sm  = ndimage.sum(z)
	return sm/tot

def rmsd(x,y,mask=None):
	return math.sqrt(msd(x,y,mask=mask))

def msd(x,y,mask=None):
	if mask != None:
		tot = float(ndimage.sum(mask))
		if tot == 0:
			return 1.0e13
		x = normStdevMask(x,mask)
		y = normStdevMask(y,mask)
	else:
		tot = float(x.shape[0]*x.shape[1])
		x = normStdev(x)
		y = normStdev(y)
	z = (x-y)**2
	if mask != None:
		z = z*mask
	sm  = ndimage.sum(z)
	return sm/tot

#########################################################
# PIL to numpy conversions
#########################################################

def imageToArray(im, convertType='uint8'):
	"""
	Convert PIL image to numpy array
	copied and modified from http://mail.python.org/pipermail/image-sig/2005-September/003554.html
	"""
	if im.mode == "L":
		a = numpy.fromstring(im.tostring(), numpy.uint8)
		a = numpy.reshape(a, (im.size[1], im.size[0]))
		#a.shape = (im.size[1], im.size[0], 1)  # alternate way
	elif (im.mode=='RGB'):
		a = numpy.fromstring(im.tostring(), numpy.uint8)
		a.shape = (im.size[1], im.size[0], 3)
	elif (im.mode=='RGBA'):
		a = numpy.fromstring(im.tostring(), numpy.uint8)
		a.shape = (im.size[1], im.size[0], 4)
	else:
		raise ValueError, im.mode+" mode not considered"

	if convertType == 'float32':
		a = a.astype(numpy.float32)
	return a

def _arrayToImage(a):
	"""
	Converts array object (numpy) to image object (PIL).
	"""
	h, w = a.shape[:2]
	boolean = numpy.bool_
	int32 = numpy.int32
	uint32 = numpy.uint32
	float32 = numpy.float32
	float64 = numpy.float64


	if a.dtype==boolean or a.dtype==int32 or a.dtype==uint32 or a.dtype==float32 or a.dtype==float64:
		a = a.astype(numpy.uint8) # convert to 8-bit

	if len(a.shape)==3:
		if a.shape[2]==3:  # a.shape == (y, x, 3)
			r = Image.fromstring("L", (w, h), a[:,:,0].tostring())
			g = Image.fromstring("L", (w, h), a[:,:,1].tostring())
			b = Image.fromstring("L", (w, h), a[:,:,2].tostring())
			return Image.merge("RGB", (r,g,b))
		elif a.shape[2]==1:  # a.shape == (y, x, 1)
			return Image.fromstring("L", (w, h), a.tostring())
	elif len(a.shape)==2:  # a.shape == (y, x)
		return Image.fromstring("L", (w, h), a.tostring())
	else:
		raise ValueError, "unsupported image mode"

def arrayToImage(numer,normalize=True):
	"""
	takes a numpy and writes a JPEG
	best for micrographs and photographs
	"""
	if normalize:
		numer = _maxNormalizeImage(numer)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	return image

def mrcToArray(filename, msg=True):
	"""
	takes a numpy and writes a Mrc
	"""
	numer = mrc.read(filename)
	if msg is True:
		apDisplay.printMsg("reading MRC: "+apDisplay.short(filename)+\
			" size:"+str(numer.shape)+" dtype:"+str(numer.dtype))
	return numer

def arrayToMrc(numer, filename, msg=True):
	"""
	takes a numpy and writes a Mrc
	"""
	#numer = numpy.asarray(numer, dtype=numpy.float32)
	if msg is True:
		apDisplay.printMsg("writing MRC: "+apDisplay.short(filename)+\
			" size:"+str(numer.shape)+" dtype:"+str(numer.dtype))
	mrc.write(numer, filename)
	return

def arrayToJpeg(numer,filename,normalize=True, msg=True):
	"""
	takes a numpy and writes a JPEG
	best for micrographs and photographs
	"""
	if normalize:
		numer = _maxNormalizeImage(numer)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	if msg is True:
		apDisplay.printMsg("writing JPEG: "+apDisplay.short(filename))
	image.save(filename, "JPEG", quality=85)
	return

def arrayToPng(numer,filename,normalize=True, msg=True):
	"""
	takes a numpy and writes a PNG
	best for masks and line art
	"""
	if normalize:
		numer = _maxNormalizeImage(numer)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	if msg is True:
		apDisplay.printMsg("writing PNG: "+apDisplay.short(filename))
	image.save(filename, "PNG")
	return

def arrayMaskToPng(numer, filename, msg=True):
	"""
	takes a numpy and writes a PNG
	best for masks and line art
	"""
	image = _arrayToImage(numer)
	#next line requires data be zero or one
	image = image.convert('1')
	if msg is True:
		apDisplay.printMsg("writing PNG mask: "+apDisplay.short(filename))
	image.save(filename, "PNG")
	return

def arrayMaskToPngAlpha(numer,filename, msg=True):
	""" 
	Create PNG file of a binary mask (array with only 0 and 1) 
	that uses the values in the alpha channel for transparency
	"""
	alpha=int(0.4*255)
	numera = numer*alpha
	numerones=numpy.ones(numpy.shape(numer))*255
	imagedummy = _arrayToImage(numerones)
	
	alphachannel = _arrayToImage(numera)

	image = imagedummy.convert('RGBA')
	image.putalpha(alphachannel)
	if msg is True:
		apDisplay.printMsg("writing alpha channel PNG mask: "+apDisplay.short(filename))
	image.save(filename, "PNG")
	return
	
def PngAlphaToBinarryArray(filename):
	alphaarray = readPNG(filename)
	masked_alphaarray = ma.masked_greater_equal(alphaarray,50)
	bmask = masked_alphaarray.filled(1)
	return alphaarray

#########################################################
# statistics of images
#########################################################

def _maxNormalizeImage(a, stdevLimit=3.0):
	"""	
	Normalizes numpy to fit into an image format,
	but maximizes the contrast
	"""
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel= 25.0,maxlevel=230.0,trim=0.1)

def _blackNormalizeImage(a, stdevLimit=3.0):
	"""	
	Normalizes numpy to fit into an image format,
	but makes it a darker than normal
	"""
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel= 0.0,maxlevel=200.0)	
def _whiteNormalizeImage(a, stdevLimit=3.0):
	"""	
	Normalizes numpy to fit into an image format,
	but makes it a lighter than normal
	"""
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel=55.0,maxlevel=255.0,trim=0.0)	

def cutEdges(img,trim=0.1):
	"""
	cut the edges of an image off by trim percent
	0.0 < trim < 1.0
	"""
	if trim >= 100.0 or trim < 0.0:
		apDisplay.printError("trim ("+str(trim)+") is out of range in cutEdges")
	elif trim >= 1.0:
		trim = trim/100.0
	elif trim == 0:
		return img
	sidetrim = trim/2.0
	xcut1 = int(img.shape[0]*sidetrim)
	ycut1 = int(img.shape[1]*sidetrim)
	xcut2 = int(img.shape[0]*(1.0-sidetrim))
	ycut2 = int(img.shape[1]*(1.0-sidetrim))
	mid = img[xcut1:xcut2,ycut1:ycut2].copy()

	return mid

def _normalizeImage(img,stdevLimit=3.0,minlevel=0.0,maxlevel=255.0,trim=0.0):
	"""	
	Normalizes numpy to fit into an image format
	that is values between 0 (minlevel) and 255 (maxlevel).
	"""
	mid = cutEdges(img,trim)

 	imrange = maxlevel - minlevel

	#GET IMAGE STATS
	avg1,stdev1,min1,max1 = getImageInfo(mid)

	#IF MIN/MAX are too high set them to smaller values
	if(min1 < avg1-stdevLimit*stdev1):
		min1 = avg1-stdevLimit*stdev1
	if(max1 > avg1+stdevLimit*stdev1):
		max1 = avg1+stdevLimit*stdev1

	if min1 == max1:
		#case of image == constant
		return img - min1

	if abs(min1) < 0.01 and abs(max1 - 1.0) < 0.01:
		#we have a mask-like object
		return img * 255

	img = (img - min1)/(max1 - min1)*imrange + minlevel
	img = numpy.where(img > maxlevel,255.0,img)
	img = numpy.where(img < minlevel,0.0,  img)

	return img


def maskImageStats(mimage):
	n=ma.count(mimage)
	mimagesq=mimage*mimage
	sum1=ma.sum(mimage)
	sum2=ma.sum(sum1)
	sumsq1=ma.sum(mimagesq)
	sumsq2=ma.sum(sumsq1)
	avg=sum2/n
	if (n > 1):
		stdev=math.sqrt((sumsq2-sum2*sum2/n)/(n-1))
	else:
		stdev=2e20
	return n,avg,stdev

def getImageInfo(im):
	"""
	prints out image information good for debugging
	"""
	avg1=ndimage.mean(im)
	stdev1=ndimage.standard_deviation(im)
	min1=ndimage.minimum(im)
	max1=ndimage.maximum(im)

	return avg1,stdev1,min1,max1

def printImageInfo(im):
	"""
	prints out image information good for debugging
	"""
	#print " ... size: ",im.shape
	#print " ... sum:  ",im.sum()
	avg1,stdev1,min1,max1 = getImageInfo(im)

	print " ... avg:  ",round(avg1,6),"+-",round(stdev1,6)
	print " ... range:",round(min1,6),"<>",round(max1,6)

	return avg1,stdev1,min1,max1

def arrayToJpegPlusPeak(numer,outfile,peak=None,normalize=True):
	"""
	takes a numpy and writes a JPEG
	best for micrographs and photographs
	"""
	if normalize:
		numer = _maxNormalizeImage(numer)
	else:
		numer = numer*255
	image = _arrayToImage(numer)
	image = image.convert("RGB")

	if peak != None:
		draw = ImageDraw.Draw(image)
		peak2 = peak.copy()
		for i in range(2):
			if peak[i] < 0:
				peak2[i] = (numer.shape)[i] + peak[i]
			elif peak[i] > (numer.shape)[i]:
				peak2[i] = peak[i] - (numer.shape)[i]
		drawPeak(peak2, draw, numer.shape)

	print " ... writing JPEG: ",outfile
	image.save(outfile, "JPEG", quality=85)

	return

def drawPeak(peak, draw, imshape, rad=10.0, color0="red", numshapes=4, shape="circle"):
	"""	
	Draws a shape around a peak
	"""

	mycolors = { 
		"red":		"#ff4040",
		"green":	"#3df23d",
		"blue":		"#3d3df2",
		"yellow":	"#f2f23d",
		"cyan":		"#3df2f2",
		"magenta":	"#f23df2",
		"orange":	"#f2973d",
		"teal":		"#3df297",
		"purple":	"#973df2",
		"lime":		"#97f23d",
		"skyblue":	"#3d97f2",
		"pink":		"#f23d97", 
	}
	row1=float(peak[1])
	col1=float(peak[0])
	#Draw (numcircs) circles of size (circmult*pixrad)
	for count in range(numshapes):
		trad = rad + count
		coord=(row1-trad, col1-trad, row1+trad, col1+trad)
		if(shape == "square"):
			draw.rectangle(coord,outline=mycolors[color0])
		else:
			draw.ellipse(coord,outline=mycolors[color0])
	updown    = (0, imshape[1]/2, imshape[0], imshape[1]/2)
	leftright = (imshape[0]/2, 0, imshape[0]/2, imshape[1])
	draw.line(updown,   fill=mycolors['blue'])
	draw.line(leftright,fill=mycolors['blue'])
	return

def readMRC(filename):
	return mrc.read(filename)

def readJPG(filename):
	i = Image.open(filename)
	i.load()
	i = imageToArray(i)
	return i

def readPNG(filename):
	i = Image.open(filename)
	i.load()
	i = imageToArray(i)
	return i

def imageToArray(im, convertType='uint8'):
	"""
	Convert PIL image to numpy array
	copied and modified from http://mail.python.org/pipermail/image-sig/2005-September/003554.html
	"""
	if im.mode == "L":
		a = numpy.fromstring(im.tostring(), numpy.uint8)
		a = numpy.reshape(a, (im.size[1], im.size[0]))
		#a.shape = (im.size[1], im.size[0], 1)  # alternate way
	elif (im.mode=='RGB'):
		a = numpy.fromstring(im.tostring(), numpy.uint8)
		a.shape = (im.size[1], im.size[0], 3)
	elif (im.mode=='RGBA'):
		atmp = numpy.fromstring(im.tostring(), numpy.uint8)
		atmp.shape = (im.size[1], im.size[0], 4)
		a = atmp[:,:,3]
	else:
		raise ValueError, im.mode+" mode not considered"

	if convertType == 'float32':
		a = a.astype(numpy.float32)
	return a




### flatfield correction functions

cache = {}
def camkey(camstate):
	return camstate['dimension']['x'], camstate['binning']['x'], camstate['offset']['x']

def getDarkNorm(sessionname, cameraconfig):
	'''
	return the most recent dark and norm image from the given session
	'''
	camquery = leginondata.CorrectorCamstateData()
	try:
		camquery['dimension'] = cameraconfig['dimension']
	except:
		pass
	try:
		camquery['binning'] = cameraconfig['binning']
	except:
		pass
	try:
		camquery['offset'] = cameraconfig['offset']
	except:
		pass
	#print 'CAMQUERY', camquery
	key = camkey(camquery) 
	if key in cache:
		print 'using cache'
		return cache[key]
	
	print 'querying dark,norm'
	sessionquery = leginondata.SessionData(name=sessionname)
	darkquery = leginondata.DarkImageData(session=sessionquery, camstate=camquery)
	#print 'DARKQUERY', darkquery
	normquery = leginondata.NormImageData(session=sessionquery, camstate=camquery)
	darkdata = db.query(darkquery, results=1)
	dark = darkdata[0]['image']
	#print darkdata[0]
	normdata = db.query(normquery, results=1)
	norm = normdata[0]['image']
	result = dark,norm
	cache[key] = result

	return result

def old_correct(input, dark, norm):
	'''
	Correct an image using the old method:
	- no bias correction
	- dark correction is not time dependent
	'''
	corrected = norm * (input - dark)
	return corrected

def frame_constant(a, shape, cval=0):
	"""
	frame_nearest creates an oversized copy of 'a' with new 'shape'
	and the contents of 'a' in the center.  The boundary pixels are
	copied from the nearest edge pixel in 'a'.

	>>> a = num.arange(16, shape=(4,4))
	>>> frame_constant(a, (8,8), cval=42)
	array([[42, 42, 42, 42, 42, 42, 42, 42],
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
