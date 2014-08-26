#!/usr/bin/env python

import sys
import time
import math
import numpy
import random
import scipy.linalg

#=================
def ellipsePoints(angleinc, center, a, b, alpha):
	'''
	Generate a sequence of x,y points given the parameters of an
	ellipse, and an angular increment.

	convention note: ellipse points are created as x,y coordinates, so alpha
		is measured as positive values towards the y-axis

	note: generate_ellipse() below is a faster version of this
	'''
	cosa = numpy.cos(alpha)
	sina = numpy.sin(alpha)
	points = []
	for angle in numpy.arange(0, 2*numpy.pi, angleinc):
		acosangle = a * numpy.cos(angle)
		bsinangle = b * numpy.sin(angle)
		row = center[0] + acosangle * cosa - bsinangle * sina
		col = center[1] + acosangle * sina + bsinangle * cosa
		points.append((row,col))
	return points

#=================
def ellipseKeyPoints(center, a, b, alpha):
	'''
	Calulate the points at each end of the ellipse axes.

	convention note: ellipse points are created as x,y coordinates, so alpha
		is measured as positive values towards the y-axis
	'''
	points = ellipsePoints(numpy.pi/2.0, center, a, b, alpha)
	keypoints = {}
	center = tuple(center)
	keypoints[center] = {'axis': 'center', 'angle': None}
	axes = ['a','b']
	for i in range(4):
		axis = axes[i%2]
		angle = alpha+i*numpy.pi/2.0
		while angle < 0:
			angle += 2*numpy.pi
		keypoints[points[i]] = {'axis': axis, 'angle': angle}
	return keypoints

#=================
def drawEllipse(shape, angleinc, center, a, b, alpha):
	'''
	Generate a zero initialized image array with an ellipse drawn
	by setting pixels to 1.

	convention note: ellipse points are x,y coordinates, so alpha
		is measured as positive values towards the y-axis
	'''
	result = numpy.zeros(shape, numpy.int)
	points = ellipsePoints(angleinc, center, a, b, alpha)
	for point in points:
		point = map(int, point)
		try:
			result[int(point[0]), int(point[1])] = 1
		except:
			continue
	return result

#=================
def algebraic2parametric(coeff):
	'''
	Based on matlab function "ellipse_param.m" which accompanies
	"Least-Squares Fitting of Circles and Ellipses", W. Gander, G. H. Golub, R. Strebel,
		BIT Numerical Mathematics, Springer 1994

	convert the coefficients (a,b,c,d,e,f) of the algebraic equation:
		ax^2 + bxy + cy^2 + dx + ey + f = 0
	to the parameters of the parametric equation.  The parameters are
	returned as a dictionary containing:
		center - center of the ellipse
		a - major axis
		b - minor axis
		alpha - angle of major axis

	convention note: alpha is measured as positive values towards the y-axis
	'''
	#print coeff
	#print ("A=%.3f B=%.3f C=%.3f D=%.3f E=%.3f F=%.3f"
	#	%(coeff[0], coeff[1], coeff[2], coeff[3], coeff[4], coeff[5],))

	if numpy.any(numpy.isnan(coeff)) or numpy.any(numpy.isinf(coeff)):
		return None

	A   = numpy.array((coeff[0], coeff[1]/2, coeff[1]/2, coeff[2]))
	A.shape = 2,2
	bb  = numpy.asarray(coeff[3:5])
	c   = coeff[5]

	D,Q = scipy.linalg.eig(A)
	D = D.real
	det = D[0]*D[1]
	if det <= 0:
		return None
	else: 
		bs = numpy.dot(Q.transpose(), bb)
		alpha = numpy.arctan2(Q[1,0], Q[0,0])

		zs = scipy.linalg.solve(-2*numpy.diagflat(D), bs)
		z = numpy.dot(Q, zs)
		h = numpy.dot(-bs.transpose(), zs) / 2 - c

		a = numpy.sqrt(h/D[0])
		b = numpy.sqrt(h/D[1])

	## correct backwards major/minor axes
	## 'major axis as a, minor axis as b'
	if b > a:
		temp = b
		b = a
		a = temp
		alpha = math.pi/2 + alpha

	#print "alpha", alpha
	if alpha <= -math.pi/2:
		alpha += math.pi
	elif alpha > math.pi/2:
		alpha -= math.pi

	return {'center':z, 'a':a, 'b':b, 'alpha':alpha}

#=================
def solveEllipseB2AC(points):
	'''
	Based on Matlab code from:  "Direct Least Square Fitting of Ellipses"
	Andrew Fitzgibbon, Maurizio Pilu, Robert B. Fisher.  Tern Analysis
	and Machine Intelligence, Vol 21, No 5, May 1999.

	This method has a tendency to crash, but is very fast
	probably should use QR decomposition to avoid crashing on singularities

	convention note: ellipse points are x,y coordinates, so alpha
		is measured as positive values towards the y-axis
	'''
	X = numpy.array(points, numpy.float)
	D = numpy.column_stack((X[:,0]**2, X[:,0]*X[:,1], X[:,1]**2, X[:,0], X[:,1], numpy.ones(X.shape[0])))
	S = numpy.dot(D.transpose(), D)
	C = numpy.zeros((6,6), numpy.float)
	C[0,2] = -2
	C[1,1] = 1
	C[2,0] = -2
	### replace eig with QR decomp
	geval,gevec = scipy.linalg.eig(a=S, b=C)
	geval = geval.real
	gevec = gevec.real

	Neg = numpy.nonzero(numpy.logical_and(geval<0, numpy.logical_not(numpy.isinf(geval))))
	a = gevec[:,Neg]
	a = numpy.ravel(a)
	
	if len(a) == 0:
		return None
	return algebraic2parametric(a)

##========================
##========================
def solveEllipseByQRdecomp(points, center=(0,0)):
	"""
	QR decomposition is not the fastest method
	but it is by far the most stable
	"""
	t0 = time.time()
	xy = numpy.array(points, dtype=numpy.float64) - numpy.array(center, dtype=numpy.float64)
	X = numpy.column_stack((
			xy[:,0]**2, 
			xy[:,0]*xy[:,1], 
			xy[:,1]**2,
		))
	Y = numpy.ones(xy.shape[0])
	### solve it by QR decomposition
	Q, R = numpy.linalg.qr(X)
	if numpy.linalg.det(R) == 0:
		print "Singular matrix in calculation"
		return None
	QT = numpy.transpose(Q)
	Rinv = numpy.linalg.inv(R)
	beta = numpy.dot(numpy.dot(Rinv, QT), Y)

	algebraic = (beta[0], beta[1], beta[2], 0, 0, -1)

	params = algebraic2parametric(algebraic)
	if params is None:
		return None

	params['center'] = center
	
	return params

##========================
def weightedLeastSquares(X, Y, W):
	"""
	solve using the normal equations with no manipulation
	"""
	### solve it
	XTW = numpy.transpose(X)*W
	XTWX = numpy.dot(XTW, X)
	if numpy.linalg.det(XTWX) == 0:
		print "Singular matrix in calculation"
		return None
	XTWXinv = numpy.linalg.inv(XTWX)
	beta = numpy.dot(numpy.dot(XTWXinv, XTW), Y)
	return beta

#=================
def totalLeastSquareEllipse(points, center=(0,0), weights=None, epsilon=1e-5, maxiter=10):
	'''
	This was implemented by Neil Voss
	
	uses simple linear least squares to solve the general equation for
	an ellipse, but implements the total least squares algorithm.
	
	http://en.wikipedia.org/wiki/Total_least_squares

	total least squares assumes some points are better than others
	so it uses an iterative approach to 
	down weight points with higher fit error
	and points with smaller error are weighed higher

	takes a (N,2) numpy array containing ellipse points and 
	return the best least square fit for an ellipse
	values A,B,C
	where
	Ax^2 + Bxy +Cy^2 + Dx + Ey + F = 0
	D = E = 0 to center the ellipse on the origin
	F = -1 to force the general conic equation to be an ellipse

	convention note: ellipse points are x,y coordinates, so alpha
		is measured as positive values towards the y-axis
	'''
	t0 = time.time()
	xy = numpy.array(points, dtype=numpy.float64) - numpy.array(center, dtype=numpy.float64)
	X = numpy.column_stack((
			xy[:,0]**2, 
			xy[:,0]*xy[:,1], 
			xy[:,1]**2,
		))
	Y = numpy.ones(xy.shape[0])

	### setup weights if necessary
	W = weights
	if W is None:
		W = numpy.ones(Y.shape) # even weights for the observations

	### solve it
	sys.stderr.write("total least squares")
	err0 = None
	for i in range(maxiter):
		sys.stderr.write(".")
		beta = weightedLeastSquares(X, Y, W)
		if beta is None:
			return None

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
	
	algebraic = (beta[0], beta[1], beta[2], 0, 0, -1)

	params = algebraic2parametric(algebraic)
	if params is None:
		return None

	params['center'] = center
	
	return params


#=================
def solveEllipseGander(points):
	'''
	Solve the ellipse that best fits the given points.
	Based on the matlab function "algellipse.m" in the files that
	accompany:  "Least-Squares Fitting of Circles and Ellipses", W. Gander, G. H. Golub, R. Strebel, 
		BIT Numerical Mathematics, Springer 1994

	This method seems to go O(n^2), so can be slow with lots of points

	convention note: ellipse points are x,y coordinates, so alpha
		is measured as positive values towards the y-axis
	'''
	X = numpy.array(points)
	a = numpy.column_stack((X[:,0]**2, X[:,0]*X[:,1], X[:,1]**2, X[:,0], X[:,1], numpy.ones(X.shape[0])))
	U, S, Vh = scipy.linalg.svd(a)
	V = Vh.transpose()
	u = numpy.ravel(V[:,5:6])
	return algebraic2parametric(u)

#=================
def solveEllipseOLS(points, center=(0,0)):
	"""
	Solve Ellipse using oridinary least squares (OLS) closed form equation

	Note: this method is designed to have the center to be 0,0 
		because the CTF is always centered

	This was implemented by Neil Voss for use in the ACE2 program in 2010
	* Algebra was performed using the maxima program
	* Designed to have a fixed center point

	takes a (N,2) numpy array containing ellipse points and 
	return the best least square fit for an ellipse
	values A,B,C
	where
	Ax^2 + Bxy +Cy^2 + Dx + Ey + F = 0
	D = E = 0 to center the ellipse on the origin
	F = -1 to force the general conic equation to be an ellipse

	convention note: ellipse points are x,y coordinates, so alpha
		is measured as positive values towards the y-axis
	"""

	### power twos
	X = numpy.array(points, numpy.float) - numpy.array(center, numpy.float)

	### power twos
	p2 = numpy.power(X, 2.0)
	Sx2 = p2[:,0].sum()
	Sy2 = p2[:,1].sum()
	Sxy = (X[:,0]*X[:,1]).sum()
	### power fours
	p4 = numpy.power(X, 4.0)
	Sx4 = p4[:,0].sum()
	Sy4 = p4[:,1].sum()
	Sx2y2 = (p2[:,0]*p2[:,1]).sum()
	Sx3y = (numpy.power(X[:,0], 3.0)*X[:,1]).sum()
	Sxy3 = (X[:,0]*numpy.power(X[:,1], 3.0)).sum()
	
	### Calculate ellipse parameters
	A = (Sx3y*(Sxy3*Sy2-Sxy*Sy4)+Sx2y2*(Sx2*Sy4+Sxy*Sxy3)
		-numpy.power(Sx2y2,2.0)*Sy2-Sx2*numpy.power(Sxy3,2.0))/(Sx4*(Sx2y2*Sy4-numpy.power(Sxy3,2.0))
		-numpy.power(Sx3y,2.0)*Sy4+2.0*Sx2y2*Sx3y*Sxy3-numpy.power(Sx2y2,3.0));
	
	B = -(Sx4*(Sxy3*Sy2-Sxy*Sy4)+Sx3y*(Sx2*Sy4-Sx2y2*Sy2)-Sx2*Sx2y2*Sxy3
		+numpy.power(Sx2y2,2.0)*Sxy)/(Sx4*(Sx2y2*Sy4-numpy.power(Sxy3,2.0))
		-numpy.power(Sx3y,2.0)*Sy4+2.0*Sx2y2*Sx3y*Sxy3-numpy.power(Sx2y2,3.0));

	C = (Sx4*(Sx2y2*Sy2-Sxy*Sxy3)-numpy.power(Sx3y,2.0)*Sy2+Sx3y*(Sx2*Sxy3+Sx2y2*Sxy)
		-Sx2*numpy.power(Sx2y2,2.0))/(Sx4*(Sx2y2*Sy4-numpy.power(Sxy3,2.0))
		-numpy.power(Sx3y,2.0)*Sy4+2.0*Sx2y2*Sx3y*Sxy3-numpy.power(Sx2y2,3.0));

	algebraic = (A, B, C, 0, 0, -1)

	params = algebraic2parametric(algebraic)
	if params is None:
		return None

	params['center'] = center

	return params

#=================
def generate_ellipse(a, b, alpha, center=(0,0), numpoints=3, noise=None, 
		method="step", integers=False):
	"""
	a - major axis radius
	b - minor axis radius
	alpha - angle (in radians)
	center = x0,y0 - position of center of ellipse
	numpoints - # of points that make an ellipse
	noise - float of the amount of noise to add

	this is a faster version of ellipsePoints() function above
		without the "for" loop and with extra features

	convention note: ellipse points are created as x,y coordinates, so alpha
		is measured as positive values towards the y-axis
	"""

	cosa = numpy.cos(alpha)
	sina = numpy.sin(alpha)

	if method == "step":
		thetas = numpy.linspace(0, 2*math.pi, numpoints)
	elif method == "random":
		thetas = numpy.random.random(numpoints) * 2*math.pi
	else:
		print "unknown method", method
		return None
	rows = center[0] + a* numpy.cos(thetas) * cosa -  b* numpy.sin(thetas) * sina
	cols = center[1] + a* numpy.cos(thetas) * sina +  b* numpy.sin(thetas) * cosa

	points = numpy.vstack((rows,cols)).T
	#print points[:5,:]

	if noise is not None:
		rand = numpy.random.standard_normal(points.shape)
		points += rand * noise
	#print points[0]

	## use only integers
	if integers is True:
		points = numpy.array(numpy.around(points, 0), dtype=numpy.int)
	#print points[0]
	#print points[:5,:]

	return points

#=================
def printParamsDict(params):
	printParams(params['center'], params['a'], params['b'], params['alpha'])
	return

#=================
def printParams(center, a, b, alpha):
	print ("%.3f %.3f < %.2f (%.1f, %.1f)"%
		(a, b, alpha*180/math.pi, center[0], center[1]))
	return

"""
Speed and accuracy notes:

NumPoints = 3777 ; Noise = 0.1 pixels
orig   5.829 1.737 < -76.84 (4.0, 16.0)
b2ac   5.813 1.747 < -76.83 (4.0, 16.0)
gander 5.834 1.740 < -76.60 (4.0, 16.0)
ols    5.833 1.753 < -76.83 (4.0, 16.0)

b2ac   complete in 8.585 millisec  ** crashes sometimes
gander complete in 924.305 millisec ** way too slow for more than 500 points
ols    complete in 5.268 millisec ** has fixed center
"""

### test code
if __name__ == '__main__':
	## randomly generate a noisy ellipse
	# note: center is (col,row) i.e. (x,y) while shape is (row,col)
	xdim = numcol = 32
	ydim = numrow = 16
	shape = (numrow,numcol)
	alpha = random.random()*math.pi - math.pi/2
	center = numpy.array((numrow, numcol), dtype=numpy.float)/2.0
	majormax = min( abs(numrow/math.cos(alpha)) , abs(numcol/math.sin(alpha)) )/3.0 - 1
	minormax = min( abs(numrow/math.sin(alpha)) , abs(numcol/math.cos(alpha)) )/3.0 - 1
	print alpha, majormax, minormax
	major = (majormax-2) * random.random() + 2
	minor = (min(minormax,major)-1) * random.random() + 1
	numpoints = 8 + int(100000*random.random()*random.random()*random.random())
	noise = 0.2 #random.random()
	print "NumPoints = %d ; Noise = %.1f"%(numpoints, noise)
	printParams(center, major, minor, alpha)

	### draw real ellipse
	points = generate_ellipse(major, minor, alpha, center, numpoints, 
		noise, method="step", integers=False)
	params = {'center':center, 'a':major, 'b':minor, 'alpha':alpha}
	grid = numpy.zeros(shape, dtype=numpy.int)
	intpoints = numpy.array(points, dtype=numpy.int)
	print intpoints
	grid[intpoints[:,0], intpoints[:,1]] = 1
	#for point in points:
	#	p = numpy.floor(point)
	#	grid[p[0],p[1]] = 1
	print grid
	print ""

	print drawEllipse(shape, 4*numpy.pi/180.0, **params)

	### draw b2ac ellipse
	t0 = time.time()
	params1 = solveEllipseB2AC(points)
	print '\nB2AC', params1
	if params1 is not None:
		print drawEllipse(shape, 4*numpy.pi/180.0, **params1)
	b2actime = time.time() - t0

	### draw gander ellipse
	t0 = time.time()
	if numpoints < 10000:
		params2 = solveEllipseGander(points)
		print '\nGANDER', params2
		print drawEllipse(shape, 4*numpy.pi/180.0, **params2)
	else:
		print "skipping GANDER"
		params2 = None
	gandertime = time.time() - t0

	### draw ols ellipse
	t0 = time.time()
	params3 = solveEllipseOLS(points, center)
	print '\nORDINARY LEAST SQUARES', params3
	print drawEllipse(shape, 4*numpy.pi/180.0, **params3)
	olstime = time.time() - t0

	### draw QR ellipse
	t0 = time.time()
	params4 = solveEllipseByQRdecomp(points, center)
	print '\nQR DECOMP', params4
	if params4 is not None:
		print drawEllipse(shape, 4*numpy.pi/180.0, **params4)
	qrdecomp = time.time() - t0

	### draw Total Least Squares ellipse
	t0 = time.time()
	params5 = totalLeastSquareEllipse(points, center)
	print '\nTotal Least Squares', params5
	if params5 is not None:
		print drawEllipse(shape, 4*numpy.pi/180.0, **params5)
	totallsq = time.time() - t0

	print majormax, minormax
	print "NumPoints = %d ; Noise = %.1f"%(numpoints, noise)
	print "Actual values"
	printParams(center, major, minor, alpha)
	print "Fit values"
	if params1 is not None:
		printParams(**params1)
	else:
		print "b2ac failed"
	if params2 is not None:
		printParams(**params2)
	else:
		print "gander skipped"
	printParams(**params3)
	if params4 is not None:
		printParams(**params4)
	else:
		print "qr decomp failed"
	if params5 is not None:
		printParams(**params5)
	else:
		print "total lsq failed"	
	print "b2ac   complete in %.3f millisec"%(b2actime*1000)
	print "gander complete in %.3f millisec"%(gandertime*1000)
	print "ols    complete in %.3f millisec"%(olstime*1000)
	print "qr     complete in %.3f millisec"%(qrdecomp*1000)
	print "total  complete in %.3f millisec"%(totallsq*1000)


