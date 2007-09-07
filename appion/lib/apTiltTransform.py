import math
import numpy
from scipy import optimize, ndimage


##
##
## Fit All Least Squares Routine
##
##


def willsq(a1, a2, \
		 theta0, gamma0=0.0, phi0=0.0, scale0=1.0, shiftx0=0.0, shifty0=0.0,\
		 xscale=numpy.ones((6), dtype=numpy.float32)):
	"""
	given two sets of particles; find the tilt, and twist of them
	"""	
	#x0 initial values
	fit = {}
	initx = numpy.array((
		theta0 * math.pi/180.0,
		gamma0 * math.pi/180.0,
		phi0   * math.pi/180.0,
		scale0,
		shiftx0,
		shifty0,
	), dtype=numpy.float32)

	#x1 delta values
	x0 = numpy.zeros(6, dtype=numpy.float32)
	#xscale scaling values
	#xscale = numpy.ones(5, dtype=numpy.float32)
	#xscale = numpy.array((1,1,1,1,1), dtype=numpy.float32)

	#print "optimizing angles and shift..."
	#print "initial rmsd:",_diffParticles(x0, initx, xscale, a1, a2)
	a1f = numpy.asarray(a1, dtype=numpy.float32)
	a2f = numpy.asarray(a2, dtype=numpy.float32)
	solved = optimize.fmin(_diffParticles, x0, args=(initx, xscale, a1f, a2f), 
		xtol=1e-4, ftol=1e-4, maxiter=500, maxfun=500, disp=0, full_output=1)
	x1 = solved[0]
	fit['rmsd'] = solved[1] #_diffParticles(x1, initx, xscale, a1, a2)
	fit['iter'] = int(solved[3])
	#print "final rmsd: "+str(fit['rmsd'])+" in "+str(fit['iter'])+" iterations"

	#x3 final values
	x3 = x1 * xscale + initx
	fit['theta']  = x3[0]*180.0/math.pi
	fit['gamma']  = x3[1]*180.0/math.pi
	fit['phi']    = x3[2]*180.0/math.pi
	fit['scale']  = x3[3]
	fit['shiftx'] = x3[4]
	fit['shifty'] = x3[5]
	fit['prob'] = math.exp(-1.0*math.sqrt(abs(fit['rmsd'])))**2
	return fit

def _diffParticles(x1, initx, xscale, a1, a2):
	x2 = x1 * xscale + initx
	theta  = x2[0]
	gamma  = x2[1]
	phi    = x2[2]
	scale  = x2[3]
	shiftx = x2[4]
	shifty = x2[5]
	a2b = a2Toa1(a1,a2,theta,gamma,phi,scale,shiftx,shifty)
	maxpix = float(len(a2b))
	diffmat = (a1 - a2b)
	xrmsd = ndimage.mean(diffmat[:,0]**2)
	yrmsd = ndimage.mean(diffmat[:,1]**2)
	rmsd = math.sqrt(xrmsd + yrmsd)/float(len(a2b))
	#print (x2*57.29).round(decimals=3),round(rmsd,6)
	return rmsd

def a1Toa2(a1,a2,theta,gamma,phi,scale, shiftx, shifty):
	a1b = a2Toa1(a2,a1,-1.0*theta,-1.0*phi,-1.0*gamma, 1.0/scale, -1.0*shiftx,-1.0*shifty)
	return a1b

def a2Toa1(a1,a2,theta,gamma,phi,scale,shiftx,shifty):
	#gamma rotation
	cosgamma = math.cos(gamma)
	singamma = math.sin(gamma)
	gammamat = numpy.array([[ cosgamma, -singamma ], [ singamma, cosgamma ]], dtype=numpy.float32)
	#theta compression
	if theta < 0:
		thetamat  = numpy.array([[ 1.0, 0.0 ], [ 0.0, math.cos(theta) ]], dtype=numpy.float32)
	else:
		thetamat  = numpy.array([[ 1.0, 0.0 ], [ 0.0, 1.0/math.cos(theta) ]], dtype=numpy.float32)
	#phi rotation
	cosphi = math.cos(phi)
	sinphi = math.sin(phi)
	phimat = numpy.array([[ cosphi, -sinphi ], [ sinphi, cosphi ]], dtype=numpy.float32)
	#scale factor
	scalemat =  numpy.array([[ scale, 0.0 ], [ 0.0, scale ]], dtype=numpy.float32)
	#merge together
	if scale > 1.0:
		trans = numpy.dot(numpy.dot(numpy.dot(scalemat,phimat),thetamat),gammamat)
	else:
		trans = numpy.dot(numpy.dot(numpy.dot(phimat,thetamat),gammamat),scalemat)
	#origins
	a10 = numpy.asarray(a1[0,:], dtype=numpy.float32)
	a20 = numpy.asarray(a2[0,:], dtype=numpy.float32)
	#convert a2 -> a1
	a2b = numpy.zeros(a2.shape, dtype=numpy.float32)
	shift = numpy.array((shiftx,shifty), dtype=numpy.float32)
	for i in range((a2.shape)[0]):
		a2c = numpy.dot(trans,a2[i,:]-a20-shift)+a10
		a2b[i,0] = a2c[0]
		a2b[i,1] = a2c[1]
	return a2b


