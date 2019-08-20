#!/usr/bin/env python

import sys
import math
import time
import numpy
from appionlib import apDisplay

"""
File of functions that solve least square problems in matrix notation:

  X * beta = Y

which is equivalent to:

  beta[1] * X[1,1] + beta[2] * X[1,2] + ... = y[1]
  beta[1] * X[2,1] + beta[2] * X[2,2] + ... = y[2]
etc.

where:
	X is in the independent variables, or N by M matrix
	beta is are the N unknown parameters to refine
	Y are the M observations or dependent variables
	W is a list a of weights of length M

typically the parameters are over determined, i.e., M >> N
"""

##========================
##========================
def numpyLeastSquares(X, Y):
	t0 = time.time()
	### check the input
	if checkMatrixSizes(X, Y) is False:
		return None

	beta, res, rank, s = numpy.linalg.lstsq(X, Y)

	apDisplay.printMsg("numpyLeastSquares completed in %s"
		%(apDisplay.timeString(time.time()-t0)))
	return beta

##========================
##========================
def numpyLeastSquaresW(X, Y, W):
	t0 = time.time()
	### check the input
	if checkMatrixSizes(X, Y) is False:
		return None

	WX = numpy.transpose( W * numpy.transpose(X) )

	beta, res, rank, s = numpy.linalg.lstsq(WX, Y)

	apDisplay.printMsg("numpyLeastSquares completed in %s"
		%(apDisplay.timeString(time.time()-t0)))
	return beta

##========================
##========================
def standardLeastSquares(X, Y):
	return leastSquaresByQRdecomp(X, Y)

##========================
##========================
def checkMatrixSizes(X, Y, W=None):
	M = X.shape[0] #m equations or observations
	N = X.shape[1] #n unknowns
	if Y.shape[0] != M:
		apDisplay.printWarning("X (%d) and Y (%d) have different M length"
			%(M, Y.shape[0]))
		return False

	if len(Y.shape) > 1 and Y.shape[1] != 1:
		apDisplay.printWarning("Y is not a vector (%d x %d)"
			%(Y.shape[0], Y.shape[1]))
		return False

	if W is None:
		## nothing else to check
		return True

	if W.shape[0] != M:
		apDisplay.printWarning("X (%d) and W (%d) have different M length"
			%(M, W.shape[0]))
		return False

	if len(W.shape) > 1 and W.shape[1] != 1:
		apDisplay.printWarning("W is not a vector (%d x %d)"
			%(W.shape[0], W.shape[1]))
		return False

	return True

##========================
##========================
def normalLeastSquares(X, Y):
	"""
	solve using the normal equations with no manipulation
	"""
	t0 = time.time()
	### check the input
	if checkMatrixSizes(X, Y) is False:
		return None
	### solve it
	XT = numpy.transpose(X)
	# create a square matrix
	XTX = numpy.dot(XT, X)
	if numpy.linalg.det(XTX) == 0:
		apDisplay.printWarning("Singular matrix in calculation")
		return None
	XTXinv = numpy.linalg.inv(XTX)
	beta = numpy.dot(numpy.dot(XTXinv, XT), Y)

	apDisplay.printMsg("normalLeastSquares completed in %s"
		%(apDisplay.timeString(time.time()-t0)))
	return beta

##========================
##========================
def leastSquaresByQRdecomp(X, Y):
	"""
	QR decomposition is not the fastest method
	but it is by far the most stable
	"""
	t0 = time.time()
	### check the input
	if checkMatrixSizes(X, Y) is False:
		return None
	### solve it by QR decomposition
	Q, R = numpy.linalg.qr(X)
	if numpy.linalg.det(R) == 0:
		apDisplay.printWarning("Singular matrix in calculation")
		return None
	QT = numpy.transpose(Q)
	Rinv = numpy.linalg.inv(R)
	beta = numpy.dot(numpy.dot(Rinv, QT), Y)
	apDisplay.printMsg("leastSquaresByQRdecomp completed in %s"
		%(apDisplay.timeString(time.time()-t0)))
	return beta

##========================
##========================
def weightedLeastSquares(X, Y, W):
	"""
	solve using the normal equations with no manipulation
	"""
	t0 = time.time()
	### check the input
	if checkMatrixSizes(X, Y) is False:
		return None
	### solve it
	XTW = numpy.transpose(X)*W
	XTWX = numpy.dot(XTW, X)
	if numpy.linalg.det(XTWX) == 0:
		apDisplay.printWarning("Singular matrix in calculation")
		return None
	XTWXinv = numpy.linalg.inv(XTWX)
	beta = numpy.dot(numpy.dot(XTWXinv, XTW), Y)
	#apDisplay.printMsg("weightedLeastSquares completed in %s"
	#	%(apDisplay.timeString(time.time()-t0)))
	return beta

##========================
##========================
def weightedLeastSquaresSVD(X, Y, W):
	"""
	solve using the Singular Value Decomposition (SVD) method

	works when matrix is singular (det = 0) but at a large computational cost

	by far the slowest method
	(1000X slower than weightedLeastSquares())

	also less accurate
	"""
	#raise NotImplementedError

	t0 = time.time()

	### check the input
	if checkMatrixSizes(X, Y) is False:
		return None

	M = X.shape[0] #m equations or observations
	N = X.shape[1] #n unknowns
	if len(Y.shape) < 2:
		Y = Y.reshape(-1, 1)
	Z = numpy.hstack([X, Y]) #adjoin matrices
	#WZ = numpy.dot(numpy.diag(W), Z)
	# this saves memory over creating the huge M by M diagonal matrix of W
	#WZ = numpy.transpose( W * numpy.transpose(Z) )
	# do the singular value decomposition
	U, S, V = numpy.linalg.svd(Z)
	VT = numpy.transpose(V)
	VXY = VT[:N,-1] # this is a vector of length N, also VXY = VT[:n,n:]
	VYY = VT[-1,-1] # this is a single scalar value, also VYY = VT[n:,n:]
	if VYY == 0:
		return None
	beta = -VXY/VYY
	apDisplay.printMsg("weightedLeastSquaresSVD completed in %s"
		%(apDisplay.timeString(time.time()-t0)))
	return beta

##========================
##========================
def totalLeastSquares(X, Y, W=None, epsilon=1e-5, maxiter=500):
	"""
	iterative refine weights of observations, de-emphasizing bad fitting points
	"""
	t0 = time.time()
	### check the input
	if checkMatrixSizes(X, Y) is False:
		return None

	### setup weights if necessary
	if W is None:
		#W = numpy.random.random((m)) # weights for the observations
		#W = W*float(M)/W.sum()
		W = numpy.ones(Y.shape) # even weights for the observations

	### solve it
	err0 = None
	sys.stderr.write("running total least squares")
	for i in range(maxiter):
		sys.stderr.write(".")
		beta = weightedLeastSquares(X, Y, W)
		if beta is None:
			if i < 2:
				return None
			beta = weightedLeastSquaresSVD(X, Y, W)

		## calculate the absolute mean error
		err = numpy.absolute(numpy.dot(X, beta) - Y).ravel()
		#print "totalLeastSquares iter %d error: %.4f"%(i, err.mean())
		## fit to a normal distribution
		normerr = ( err - err.min() )/err.std()
		## calculate new weights based on 
		W = numpy.exp( -1 * normerr**2 )
		if W.sum() == 0:
			apDisplay.printWarning("Failed to set weights")
			return beta
		## see if we can stop
		if err0 is not None:
			change = numpy.absolute(err-err0).mean()
			if change < epsilon:
				break
		err0 = err
	apDisplay.printMsg("totalLeastSquares completed in %s in %d iterations"
		%(apDisplay.timeString(time.time()-t0), i))
	return beta

##========================
##========================
##========================
##========================
if __name__ == "__main__":
	## setup least squares and solve it bunch of times
	## equation y = a * x^2 + b x + c
	xvec = numpy.arange(0, 100, 1e-2, dtype=numpy.float64)
	beta0 = numpy.array([7e-3, -1, 36], dtype=numpy.float64)
	onevec = numpy.ones(xvec.shape, dtype=numpy.float64)
	X = numpy.array([xvec**2, xvec, onevec]).transpose()
	Y = numpy.dot(X, beta0) + numpy.random.normal(0, 1, xvec.shape)
	W = numpy.ones(Y.shape)

	print "numpyLeastSquares", ((numpyLeastSquares(X, Y)-beta0)**2).mean()
	print "numpyLeastSquaresW", ((numpyLeastSquaresW(X, Y, W)-beta0)**2).mean()
	print "normalLeastSquares", ((normalLeastSquares(X, Y)-beta0)**2).mean()
	print "leastSquaresByQRdecomp", ((leastSquaresByQRdecomp(X, Y)-beta0)**2).mean()
	print "weightedLeastSquares", ((weightedLeastSquares(X, Y, W)-beta0)**2).mean()
	print "weightedLeastSquaresSVD", ((weightedLeastSquaresSVD(X, Y, W)-beta0)**2).mean()
	print "totalLeastSquares", ((totalLeastSquares(X, Y, W, maxiter=4)-beta0)**2).mean()










