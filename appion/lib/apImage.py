#Part of the new pyappion

import math
import imagefun
import convolver
import Image
import numarray
import numarray.nd_image as nd_image
import numarray.linear_algebra as linear_algebra

def preProcessImage(img,bin=1,apix=1.0,lowpass=0.0,planeReg=True):
	img = binImg(img,bin)
	if planeReg:
		img = planeRegression(img)
	img = lowPassFilter(img,apix,bin,lowpass)
	img = 255.0*(normRange(img)+1.0e-7)
	return img

def binImg(img,bin=1):
	"""
	returns a binned image
	"""
	if bin > 1:
		return imagefun.bin(img,bin)
	else:
		return img

def filterImg(img,apix=1.0,bin=1,radius=0.0):
	#TEMPORARY ALIAS
	return lowPassFilter(img,apix,bin,rad)

def lowPassFilter(img,apix=1.0,bin=1,radius=0.0):
	"""
	low pass filter image to radius resolution
	"""
	if radius==0:
		print " ... skipping low pass filter"
		return(img)
	else:
		print " ... performing low pass filter"
		sigma=float(radius)/apix/3.0/float(bin)
		kernel=convolver.gaussian_kernel(sigma)
	c=convolver.Convolver()
	return(c.convolve(image=img,kernel=kernel))

def planeRegression(img):
	"""
	performs a two-dimensional linear regression and subtracts it from an image
	"""
	#print " ... calculate 2d linear regression"
	if ( (img.shape)[0] != (img.shape)[1] ):
		print "Array is NOT square"
		sys.exit(1)
	size = (img.shape)[0]
	count = float((img.shape)[0]*(img.shape)[1])
	def retx(y,x):
		return x
	def rety(y,x):
		return y	
	xarray = numarray.fromfunction(retx, img.shape)
	yarray = numarray.fromfunction(rety, img.shape)
	xsum = float(xarray.sum())
	xsumsq = float((xarray*xarray).sum())
	ysum = xsum
	ysumsq = xsumsq
	xysum = float((xarray*yarray).sum())
	xzsum = float((xarray*img).sum())
	yzsum = float((yarray*img).sum())
	zsum = img.sum()
	zsumsq = (img*img).sum()
	xarray = xarray.astype(numarray.Float64)
	yarray = yarray.astype(numarray.Float64)
	leftmat = numarray.array( [[xsumsq, xysum, xsum], [xysum, ysumsq, ysum], [xsum, ysum, count]] )
	rightmat = numarray.array( [xzsum, yzsum, zsum] )
	resvec = linear_algebra.solve_linear_equations(leftmat,rightmat)
	print " ... plane_regress: x-slope:",round(resvec[0]*size,5),\
		", y-slope:",round(resvec[1]*size,5),", xy-intercept:",round(resvec[2],5)
	newarray = img - xarray*resvec[0] - yarray*resvec[1] - resvec[2]
	del img,xarray,yarray,resvec
	return newarray

def normRange(img):
	min1=nd_image.minimum(img)
	max1=nd_image.maximum(img)
	if min1 == max1:
		return img - min1
	return (img - min1)/(max1 - min1)

def normStdev(img):
	avg1=nd_image.mean(img)
	std1=nd_image.standard_deviation(img)
	if std1 == 0:
		return img - avg1
	return (img - avg1)/std1

def normStdevMask(img,mask):
	n1     = nd_image.sum(mask)
	if n1 == 0:
		return img
	sum1   = nd_image.sum(img*mask)
	sumsq1 = nd_image.sum(img*img*mask)
	avg1   = sum1/n1
	std1   = math.sqrt((sumsq1 - sum1*sum1/n1)/(n1-1))
	std2   = nd_image.standard_deviation(img)
	return (img - avg1) / std1

#########################################################

def correlationCoefficient(x,y,mask=None):
	if x.shape != y.shape:
		print "ERROR: images are not the same shape"
		return 0.0
	if mask != None:
		if x.shape != mask.shape:
			print "ERROR: mask is not the same shape as images"
			return 0.0
		tot = nd_image.sum(mask)
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
	sm  = nd_image.sum(z)
	return sm/tot

#########################################################

def imageToArray(im, convertType='UInt8'):
    """
    Convert PIL image to Numarray array
    copied and modified from http://mail.python.org/pipermail/image-sig/2005-September/003554.html
    """
    if im.mode == "L":
        a = numarray.fromstring(im.tostring(), numarray.UInt8)
        a = numarray.reshape(a, (im.size[1], im.size[0]))
        #a.shape = (im.size[1], im.size[0], 1)  # alternate way
    elif (im.mode=='RGB'):
        a = numarray.fromstring(im.tostring(), numarray.UInt8)
        a.shape = (im.size[1], im.size[0], 3)
    else:
        raise ValueError, im.mode+" mode not considered"

    if convertType == 'Float32':
        a = a.astype(numarray.Float32)
    return a

def arrayToJpeg(numer,filename):
	if numer.max()-numer.min() >0.1:
		numer = _maxNormalizeImage(numer)
	image = _arrayToImage(numer)
	print " ... writing JPEG: ",filename
	image.save(filename, "JPEG", quality=85)
	return

def arrayToPng(numer,filename):
	if numer.max()-numer.min() >0.1:
		numer = _maxNormalizeImage(numer)
	image = _arrayToImage(numer)
	print " ... writing Png: ",filename
	image.save(filename, "PNG")
	return

def _maxNormalizeImage(a, stdevLimit=3.0):
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel= 25.0,maxlevel=230.0,trim=0.1)
def _blackNormalizeImage(a, stdevLimit=3.0):
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel= 0.0,maxlevel=200.0)	
def _whiteNormalizeImage(a, stdevLimit=3.0):
	return _normalizeImage(a,stdevLimit=stdevLimit,minlevel=55.0,maxlevel=255.0,trim=0.0)	

def _normalizeImage(img,stdevLimit=3.0,minlevel=0.0,maxlevel=255.0):
	"""	
	Normalizes numarray to fit into an image format
	that is values between 0 (minlevel) and 255 (maxlevel).
	"""
	if trim > 0.0:
		xcut1 = img.shape[0]*trim
		ycut2 = img.shape[1]*trim
		xcut1 = img.shape[0]*(1.0-trim)
		ycut2 = img.shape[1]*(1.0-trim)
		mid = img[xcut1:xcut2,ycut1,ycut2]
	else:
		mid = img

 	imrange = maxlevel - minlevel
	avg1=nd_image.mean(mid)
	stdev1=nd_image.standard_deviation(mid)

	min1=nd_image.minimum(mid)
	if(min1 < avg1-stdevLimit*stdev1):
		min1 = avg1-stdevLimit*stdev1

	max1=nd_image.maximum(mid)
	if(max1 > avg1+stdevLimit*stdev1):
		max1 = avg1+stdevLimit*stdev1

	img = (img - min1)/(max1 - min1)*imrange + minlevel
	img = numarray.where(img > maxlevel,255.0,img)
	img = numarray.where(img < minlevel,0.0,  img)

	return a

def _arrayToImage(a):
    """
    Converts array object (numarray) to image object (PIL).
    """
    h, w = a.shape[:2]
    boolean = numarray.Bool
    int32 = numarray.Int32
    uint32 = numarray.UInt32
    float32 = numarray.Float32
    float64 = numarray.Float64

    if a.type()==boolean or a.type()==int32 or a.type()==uint32 or a.type()==float32 or a.type()==float64:
        a = a.astype(numarray.UInt8) # convert to 8-bit
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
