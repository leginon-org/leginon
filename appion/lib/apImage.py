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

######################################################################
# Convexhull related functions Starts
######################################################################

"""Taken from internet
   , strip down to needed parts and add Colinear test and complete the polygon
   with the initial point if lacked
Anchi"""

"""Calculate the convex hull of a set of n 2D-points in O(n log n) time.  
Taken from Berg et al., Computational Geometry, Springer-Verlag, 1997.
Dinu C. Gherman
"""

def _myDet(p, q, r):
	"""Calc. determinant of a special matrix with three 2D points.

	The sign, "-" or "+", determines the side, right or left,
	respectivly, on which the point r lies, when measured against
	a directed vector from p to q.
	"""

	# We use Sarrus' Rule to calculate the determinant.
	# (could also use the Numeric package...)
	sum1 = q[0]*r[1] + p[0]*q[1] + r[0]*p[1]
	sum2 = q[0]*p[1] + r[0]*q[1] + p[0]*r[1]

	return sum1 - sum2


def _isRightTurn((p, q, r)):
	"""Do the vectors pq:qr form a right turn, or not?"""

	assert p != q and q != r and p != r
			
	if _myDet(p, q, r) < 0:
		return 1
	else:
		return 0

def _isRightTurnOrColinear((p, q, r)):
	"""Do the vectors pq:qr form a right turn, or not?"""
	assert p != q and q != r and p != r
	if _myDet(p, q, r) < 0:
		return 1
	else:
		if _myDet(p, q, r) > 0:
			return 0
		if _myDet(p, q, r) == 0:
			if ((p[0]<= q[0] and r[0]>=q[0]) or (p[0]>= q[0] and r[0]<=q[0])) and ((p[1]<= q[1] and r[1]>=q[1]) or (p[1]>= q[1] and r[1]<=q[1])):
				return 1
			else:
				return 0

def isPointInPolygon(r, P0):
	"""Is point r inside or on the edge of a given polygon P?"""
	# We assume the polygon is a list of points, listed clockwise!
	P=list(P0)
	if (P[0] !=P[-1]):
		P.append(P[0])
	for i in xrange(len(P[:-1])):
		p, q = P[i], P[i+1]
		if not (r==p or r==q):
			if not _isRightTurnOrColinear((p, q, r)):
				return 0 # Out!		   
	return 1 # It's within or on!

def _isPointOnlyInPolygon(r, P0):
	"""Is point r inside a given polygon P?"""
	# We assume the polygon is a list of points, listed clockwise!
	P=list(P0)
	if (P[0] !=P[-1]):
		P.append(P[0])
	for i in xrange(len(P[:-1])):
		p, q = P[i], P[i+1]
		if (r==p or r==q):
			return 1 # It's on
		else:
			if not _isRightTurn((p, q, r)):
				return 0 # Out!		   

	return 1 # It's within!

def convexHull(P):
	"""Calculate the convex hull of a set of points."""

	# Get a local list copy of the points and sort them lexically.
	points = map(None, P)
	points.sort()

	# Build upper half of the hull.
	upper = [points[0], points[1]]
	for p in points[2:]:
		upper.append(p)
		while len(upper) > 2 and not _isRightTurnOrColinear(upper[-3:]):
			del upper[-2]

	# Build lower half of the hull.
	points.reverse()
	lower = [points[0], points[1]]
	for p in points[2:]:
		lower.append(p)
		while len(lower) > 2 and not _isRightTurnOrColinear(lower[-3:]):
			del lower[-2]

	# Remove duplicates.
	del lower[0]
	del lower[-1]

	# Concatenate both halfs and return.
	return tuple(upper + lower)

######################################################################
# Convexhull related functions Ends
######################################################################
