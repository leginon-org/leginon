#Part of the new pyappion

import imagefun
import convolver
import numarray
import numarray.linear_algebra as linear_algebra

def binImg(img,bin=1):
	"""
	returns a binned image
	"""
	return imagefun.bin(img,bin)

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
	print " ... calculate 2d linear regression"
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
	del leftmat,rightmat
	print " ... plane_regress: x-slope:",round(resvec[0]*size,5),\
		", y-slope:",round(resvec[1]*size,5),", xy-intercept:",round(resvec[2],5)
	newarray = img - xarray*resvec[0] - yarray*resvec[1] - resvec[2]
	del img,xarray,yarray,resvec
	return newarray


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
