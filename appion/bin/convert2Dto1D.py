#!/usr/bin/env python

import os
import math
import numpy
from pyami import mrc, imagefun
from scipy import special
from appionlib.apSpider import operations

"""
The goal of this function is to create a function, f(r),
 that will generate the original 2D envelopeImage.mrc

The function will contain 1D points and use linear interpolation
 to fill in the gaps. The function is also monotonically decreasing.

Numpy has an linear interpolation function: numpy.interp
 http://docs.scipy.org/doc/numpy/reference/generated/numpy.interp.html

Scipy has non-linear interpolation functions: scipy.interpolate
 http://docs.scipy.org/doc/scipy/reference/interpolate.html
 including cubic spline, which is probably ideal.

I need to decide the resolution of the 1D and 
 I decided that 1 pixel was enough ranging between 0 and 2896
 to fill a complete 4k image

Create two numpy arrays one for sums and a second for weight. Loop through all
 pixels and make their contribution to the relevant pixels (+/- 3 pixels). 
 At the end, divide the sums by the weights and we obtain the 1D function, f(r).

For each integer in r, I will then calculate a mean based on all nearby values
 +/- 2 pixels. Probably with a Gaussian weighting, error function in python
 from scipy.special import erfc
 weight = erfc( abs(r-r_i)/Sqrt(2) )

F[0] = 265.20575 based on linear extrapolation involving first 4 points
F[2896] = 185.45721 based on linear extrapolation involving last 4 points

"""

#=================
def fromRadialFunc(funcrad, shape, **kwargs):
	center_r = (shape[0] - 1)/2.0
	center_c = (shape[1] - 1)/2.0
	def funcrc(r, c, **kwargs):
		rr = r - center_r
		cc = c - center_c
		rad = numpy.hypot(rr,cc)
		return funcrad(rad, **kwargs)
	result = numpy.fromfunction(funcrc, shape, **kwargs)
	return result

#=================
def funcrad(r, xdata=None, rdata=None):
	#print xdata.shape, rdata.shape
	z = numpy.interp(r, xdata, rdata)
	#print z
	return z	

#=================
def run():
	env = mrc.read("/home/vossman/myami/appion/appionlib/data/envelopeImage.mrc")
	#env = imagefun.bin2(env, 16)
	print env.shape
	xcenter = (env.shape[0] - 1)/2.0
	ycenter = (env.shape[1] - 1)/2.0
	radialsize = int(math.ceil(max(env.shape[0], env.shape[1])/math.sqrt(2.0)))
	sums = numpy.zeros((radialsize), dtype=numpy.float64)
	weights = numpy.zeros((radialsize), dtype=numpy.float64)
	### deal with end points
	for deltaradius in range(4):
		### double weight for ends
		weight = 2.0*special.erfc( deltaradius/math.sqrt(2.0) )
		### zero end
		sums[deltaradius] += weight*265.20575
		weights[deltaradius] += weight
		### tail end
		sums[2896-deltaradius] += weight*185.45721
		weights[2896-deltaradius] += weight
	### read data and apply
	for x in range(env.shape[0]):
		if x % 100 == 0:
			print x
		for y in range(env.shape[1]):
			radius = math.hypot(x - xcenter, y - ycenter)
			intesity = env[x,y]
			for deltaradius in range(-3,4):
				pixelradius = int(round(radius + deltaradius))
				if pixelradius < 0 or pixelradius > radialsize-1:
					continue
				distance = abs(radius - pixelradius)
				weight = special.erfc( distance/math.sqrt(2.0) )
				sums[pixelradius] += weight*intesity
				#sumsquares[pixelradius] += weight*intesity*intesity
				weights[pixelradius] += weight
	rdata = sums/weights
	#print 0, rdata[0], "-->", 265.20575
	#print 2896, rdata[2896], "-->", 185.45721
	rdata[0] = 265.20575
	rdata[2896] = 185.45721
	f = open('radial-envelope.numpy', 'wb')
	rdata.dump(f)
	f.close()

	return rdata

#=================
def test(rdata):
	radialsize = rdata.shape[0]
	envshape = (4096, 4096)
	### write data out
	f = open('radial-envelope.dat', 'w')
	spi = open('radial-envelope.spi', 'w')
	for i in range(radialsize):
		f.write('%d\t%.8f\n'%(i, rdata[i]))
		spi.write(operations.spiderOutLine(i, [i, rdata[i]]))
	f.close()
	spi.close()

	### create new mrc
	xdata = numpy.arange(0, radialsize, 1.0, dtype=numpy.float64)
	### fixed end values
	#print 0, rdata[0], "-->", 265.20575
	#print 2896, rdata[2896], "-->", 185.45721
	rdata[0] = 265.20575
	rdata[2896] = 185.45721
	envcalc = fromRadialFunc(funcrad, envshape, xdata=xdata, rdata=rdata)
	mrc.write(envcalc, 'calcualted-envelope.mrc')

#=================
if __name__ == "__main__":
	if os.path.isfile('radial-envelope.numpy'):
		f = open('radial-envelope.numpy', 'rb')
		rdata = numpy.load(f)
		f.close()
	else:
		rdata = run()
	test(rdata)

