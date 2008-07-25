#!/usr/bin/env python

import numpy
import pyami.quietscipy
from scipy.optimize import leastsq

def gaussian(sigma, a, b, dr, dc, r, c):
	return b + a * numpy.exp(-((r-dr)**2+(c-dc)**2) / 2.0 / sigma**2)

def gaussian_image(shape, sigma, a, b, dr, dc):
	rows,cols = numpy.indices(shape)
	return gaussian(sigma, a, b, dr, dc, rows, cols)

def gaussian_residual(unknowns, r, c, z):
	#return 1.0 / (2.0 * numpy.pi * sigma**2) * numpy.exp(-(r**2+c**2) / 2.0 / sigma**2)
	sigma,a,b,dr,dc = unknowns
	#r,c,z = args
	x = gaussian(sigma, a, b, dr, dc, r, c) - z
	#print 'X', x
	return x.flat

def gaussfit(im):
	r,c = numpy.indices(im.shape)
	estimate = 1.0, 1.0, 0.0, im.shape[0]/2, im.shape[1]/2
	args = r, c, im
	result = leastsq(gaussian_residual, estimate, args)
	result = result[0]

	residuals = gaussfit_residuals(im, result)
	chisquare = numpy.sum(residuals**2)

	return result, residuals, chisquare

def gaussfit_residuals(im, solution):
	im2 = gaussian_image(im.shape, *solution)
	residuals = im2 - im
	return residuals

if __name__ == '__main__':
	import numpy.random
	testim = numpy.random.normal(1,1,(5,5))
	#testim = gaussian_image((5,5), 1.0, 2, 1.5, 3.5, 2.3)
	print 'TESTIM', testim
	'''
	testim[4,4] += 1.1
	print 'TESTIM', testim
	'''
	solution = gaussfit(testim)
	print 'SOLUTION', solution
