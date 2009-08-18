#!/usr/bin/env python
import numpy
import scipy.linalg

def ellipsePoints(angleinc, center, a, b, alpha):
	'''
	Generate a sequence of x,y points given the parameters of an
	ellipse, and an angular increment.
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

def ellipseKeyPoints(center, a, b, alpha):
	'''
	Calulate the points at each end of the ellipse axes.
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
	print 'KEYPOINTs', keypoints
	return keypoints

def drawEllipse(shape, angleinc, center, a, b, alpha):
	'''
	Generate a zero initialized image array with an ellipse drawn
	by setting pixels to 1.
	'''
	result = numpy.zeros(shape, numpy.int)
	points = ellipsePoints(angleinc, center, a, b, alpha)
	for point in points:
		point = map(int, point)
		result[int(point[0]), int(point[1])] = 1
		try:
			result[int(point[0]), int(point[1])] = 1
		except:
			pass
	return result


def algebraic2parametric(coeff):
	'''
	Based on matlab function "ellipse_param.m" which accompanies
	"Least-Squares Fitting of Circles and Ellipses", W. Gander, G. H. Golub, R. Strebel, BIT Numerical Mathematics, Springer 1994

	convert the coefficients (a,b,c,d,e,f) of the algebraic equation:
		ax^2 + bxy + cy^2 + dx + ey + f = 0
	to the parameters of the parametric equation.  The parameters are
	returned as a dictionary containing:
		center - center of the ellipse
		a - major axis
		b - minor axis
		alpha - angle of major axis
	'''

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
	return {'center':z, 'a':a, 'b':b, 'alpha':alpha}

def solveEllipseB2AC(points):
	'''
	Based on Matlab code from:  "Direct Least Square Fitting of Ellipses"
	Andrew Fitzgibbon, Maurizio Pilu, Robert B. Fisher.  Tern Analysis
	and Machine Intelligence, Vol 21, No 5, May 1999.
	'''
	X = numpy.array(points, numpy.float)
	D = numpy.column_stack((X[:,0]**2, X[:,0]*X[:,1], X[:,1]**2, X[:,0], X[:,1], numpy.ones(X.shape[0])))
	S = numpy.dot(D.transpose(), D)
	C = numpy.zeros((6,6), numpy.float)
	C[0,2] = -2
	C[1,1] = 1
	C[2,0] = -2
	geval,gevec = scipy.linalg.eig(a=S, b=C)
	geval = geval.real
	gevec = gevec.real

	Neg = numpy.nonzero(numpy.logical_and(geval<0, numpy.logical_not(numpy.isinf(geval))))
	a = gevec[:,Neg]
	a = numpy.ravel(a)
	return algebraic2parametric(a)

def solveEllipseGander(points):
	'''
	Solve the ellipse that best fits the given points.
	Based on the matlab function "algellipse.m" in the files that
	accompany:  "Least-Squares Fitting of Circles and Ellipses", W. Gander, G. H. Golub, R. Strebel, BIT Numerical Mathematics, Springer 1994
	'''
	X = numpy.array(points)
	a = numpy.column_stack((X[:,0]**2, X[:,0]*X[:,1], X[:,1]**2, X[:,0], X[:,1], numpy.ones(X.shape[0])))
	U, S, Vh = scipy.linalg.svd(a)
	V = Vh.transpose()
	u = numpy.ravel(V[:,5:6])
	return algebraic2parametric(u)

### test code
if __name__ == '__main__':
	## draw a rectangle on an image and fit an ellipse to it
	drawing = numpy.zeros((20,20), numpy.int)
	drawing[5,5:15] = 1
	drawing[9,5:15] = 1
	drawing[5:9,5] = 1
	drawing[5:9,15] = 1
	print drawing
	points = numpy.nonzero(drawing)
	points = numpy.array(points)
	points = points.transpose()
	params1 = solveEllipseB2AC(points)
	params2 = solveEllipseGander(points)

	print 'B2AC', params1
	print drawEllipse((20,20), 10*numpy.pi/180.0, **params1)

	print 'GANDER', params2
	print drawEllipse((20,20), 10*numpy.pi/180.0, **params2)
