# Copyright 2004-2008 by M de Hoon.
# Copyright 2011 Neil Voss
# This code was orignally part of the Biopython distribution

"""
This module implements the Lowess function for nonparametric regression.

Functions:
lowess        Fit a smooth nonparametric regression curve to a scatterplot.

For more information, see

William S. Cleveland: "Robust locally weighted regression and smoothing
scatterplots", Journal of the American Statistical Association, December 1979,
volume 74, number 368, pp. 829-836.

William S. Cleveland and Susan J. Devlin: "Locally weighted regression: An
approach to regression analysis by local fitting", Journal of the American
Statistical Association, September 1988, volume 83, number 403, pp. 596-610.
"""

import math
import numpy

#==================
def distance(x, smoothing, h):
	dx,dy = numpy.meshgrid(x,x)
	#raw distances
	d = abs(dx-dy)
	d = d/h
	d = numpy.clip(d,0.0,1.0)
	print "x=", numpy.around(x,2)
	print "h=", numpy.around(h,2)
	print "d=", numpy.around(d,2)
	print "dsum=", numpy.around(d.sum(1),2)

#==================
def getSmoothingSorted(x, smoothing):
	### calculate smoothing
	n = len(x)
	r = int(math.ceil(smoothing*n))
	rhalf = int(math.ceil(smoothing*n/2))
	#print "r=", r
	#print "x(sort)=", numpy.sort(x)
	xsort = numpy.sort(x)
	xstart = min(r+1,rhalf)
	xend = max(r+1,rhalf)
	space = numpy.ones( (n-(xend-xstart)*2) )*xsort[xstart]
	filler = xsort[xstart:xend]
	h = numpy.hstack( (filler[::-1], space, filler) )
	### may be able to use argsort to unsort the h array
	#print "h=", numpy.around(h,2)
	### provides how to sort, need to unsort, so argsort twice
	#print "x=", numpy.around( x[numpy.argsort(x)] ,2)
	h = h[ numpy.argsort(numpy.argsort(x)) ]
	#print "h=", numpy.around(h,2)
	return h

#==================
def getSmoothingRaw(x, smoothing):
	n = len(x)
	r = int(numpy.ceil(smoothing*n))
	h = [numpy.sort(abs(x-x[i]))[r] for i in range(n)]
	#print "h=", numpy.around(h,2)
	return h

#==================
def lowess(x, y, smoothing=0.667, iter=3):
	"""lowess(x, y, f=2./3., iter=3) -> yest

	Lowess smoother: Robust locally weighted regression.
	The lowess function fits a nonparametric regression curve to a scatterplot.
	The arrays x and y contain an equal number of elements; each pair
	(x[i], y[i]) defines a data point in the scatterplot. The function returns
	the estimated (smooth) values of y.

	The smoothing span is given by float. A larger value for smoothing will result in a
	smoother curve. The number of robustifying iterations is given by iter. The
	function will run faster with a smaller number of iterations.

	x and y should be numpy float arrays of equal length.  The return value is
	also a numpy float array of that length.

	e.g.
	>>> import numpy
	>>> x = numpy.array([4,  4,  7,  7,  8,  9, 10, 10, 10, 11, 11, 12, 12, 12,
	...                 12, 13, 13, 13, 13, 14, 14, 14, 14, 15, 15, 15, 16, 16,
	...                 17, 17, 17, 18, 18, 18, 18, 19, 19, 19, 20, 20, 20, 20,
	...                 20, 22, 23, 24, 24, 24, 24, 25], numpy.float)
	>>> y = numpy.array([2, 10,  4, 22, 16, 10, 18, 26, 34, 17, 28, 14, 20, 24,
	...                 28, 26, 34, 34, 46, 26, 36, 60, 80, 20, 26, 54, 32, 40,
	...                 32, 40, 50, 42, 56, 76, 84, 36, 46, 68, 32, 48, 52, 56,
	...                 64, 66, 54, 70, 92, 93, 120, 85], numpy.float)
	>>> result = lowess(x, y)
	>>> len(result)
	50
	>>> print "[%0.2f, ..., %0.2f]" % (result[0], result[-1])
	[4.85, ..., 84.98]
	"""
	#print "x(shape)=", x.shape
	#print "y(shape)=", y.shape
	#print "smoothing=%.3f"%(smoothing)
	#print "numiter=%d"%(iter)
	#print "x=", numpy.around(x,2)
	#print "y=", numpy.around(y,2)
	n = len(x) #x.shape[0]

	### calculate smoothing
	if (abs(x - numpy.sort(x))).sum() < 1e-6:
		#print "sort smoothing"
		h = getSmoothingSorted(x, smoothing)
	else:
		#print "raw smoothing"
		h = getSmoothingSorted(x, smoothing)
		#h = getSmoothingRaw(x, smoothing)

	### get weight distribution
	# numbers must be between zero and one
	# gets a distance
	w = numpy.clip(abs(([x]-numpy.transpose([x])))/h,0.0,1.0)
	#print "w=", numpy.around(w,2)
	w = 1-w*w*w
	w = w*w*w
	#print "w=", numpy.around(w,2)
	#d = distance(x, smoothing, h)
	#print "d=", numpy.around(d,2)
	#sys.exit(1)
	fit = numpy.zeros(n)
	delta = numpy.ones(n)
	for iteration in range(iter):
		for i in xrange(n):
			weights = delta * w[:,i]
			weights_mul_x = weights * x
			b = numpy.array([(weights*y).sum(), (weights*y*x).sum()])
			sumx = (weights*x).sum()
			A = numpy.array([[weights.sum(), sumx], [sumx, (weights*x*x).sum()]])
			beta = numpy.linalg.solve(A,b)
			fit[i] = beta[0] + beta[1]*x[i]

		residuals = y-fit
		s = numpy.median(abs(residuals))
		#print "residuals=", numpy.around(residuals,2)
		delta[:] = numpy.clip(residuals/(6*s),-1,1)
		delta[:] = 1-delta*delta
		delta[:] = delta*delta
	return fit

def _test():
	"""Run the Bio.Statistics.lowess module's doctests."""
	print "Running doctests..."
	import doctest
	doctest.testmod()
	print "Done"

if __name__ == "__main__":
	_test()
