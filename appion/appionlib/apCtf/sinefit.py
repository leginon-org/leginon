#!/usr/bin/env python

import math
import time
import numpy
import scipy.stats
from appionlib import apDisplay
from appionlib.apImage import imagestat
from appionlib.apCtf import ctftools, genctf, leastsq

#===================================================
#===================================================
#===================================================
def refineAmplitudeContrast(radial_array, defocus, normPSD, cs, wavelength, weights=None, msg=True):
	"""
	takes elliptical average data and fits it to the equation
	A cos(x) + B sin(x)
	"""

	if msg is True:
		print "resolution limits %.2f <> %.2f"%(1.0e10/radial_array.max(), 1.0e10/radial_array.min())

	# create X matrix
	radialsq = radial_array**2
	if msg is True:
		print 1.0/radial_array[-1], wavelength, defocus, cs
	gamma = ( -0.5 * math.pi * cs * wavelength**3 * radialsq**2
		+ math.pi * wavelength * radialsq * defocus )
	cosvec = numpy.cos(2*gamma) #C
	sinvec = numpy.sin(2*gamma) #D
	onevec = numpy.ones(gamma.shape) #extra constant
	X = numpy.array([cosvec, sinvec, onevec, radialsq]).transpose()
	#del cosvec, sinvec, gamma

	# create weighted matrix
	if weights is None:
		# make an identity matrix for no weights
		weights = numpy.ones(normPSD.shape[0])

	# adjust y values
	yprime = (normPSD - normPSD.mean())
	yprime /= numpy.abs(yprime).max()

	## solve it
	beta = leastsq.totalLeastSquares(X, yprime, weights)
	if beta is None:
		beta = leastsq.numpyLeastSquares(X, yprime)
	del X, weights
	if beta is None:
		apDisplay.printWarning("Least squares failed")
		return None

	#translate the values
	C = beta[0]
	D = beta[1]
	constant = beta[2]
	sqterm = beta[3]
	if msg is True:
		print beta, radial_array.shape
	psi = 0.5*math.atan2(C,D)
	if msg is True:
		print "psi=", psi
	phi = psi + math.pi/4
	if msg is True:
		print "phi=", phi
	amp_con = math.sin(phi)

	if msg is True:
		apDisplay.printColor("amplitude contrast = %.8f"%(amp_con), "cyan")

	fitctf1 = C*cosvec + D*sinvec
	fitctf2 = numpy.sin(2*gamma + 2*psi)
	newB = math.sqrt(1 - amp_con**2)
	# need to do the y' = 2 y - 1
	adjctf1 = 2 * numpy.power(amp_con*numpy.cos(gamma) + newB*numpy.sin(gamma), 2) - 1
	#adjctf2 = 2 * numpy.power(numpy.sin(gamma + math.asin(amp_con)), 2) - 1

	crosscorr = scipy.stats.pearsonr(fitctf2, adjctf1)[0]
	yprime2 = yprime - constant - sqterm*radialsq
	yprime2 /= numpy.abs(yprime2).max()
	fitconf = scipy.stats.pearsonr(yprime2, fitctf2)[0]

	if msg is True:
		from matplotlib import pyplot
		pyplot.clf()

		pyplot.plot(radialsq, yprime2, '.', color="gray")
		pyplot.plot(radialsq, yprime2, 'k-',)
		pyplot.plot(radialsq, fitctf1, 'r--',)
		pyplot.plot(radialsq, fitctf2, 'g--',)
		pyplot.plot(radialsq, adjctf1, 'b--',)

		conf1 = scipy.stats.pearsonr(yprime2, fitctf1)[0]
		conf2 = scipy.stats.pearsonr(yprime2, adjctf1)[0]
		conf3 = scipy.stats.pearsonr(yprime2, fitctf2)[0]

		print "conf %.4f, %.4f, %.4f; cc = %.4f"%(conf1, conf2, conf3, crosscorr)

		#pyplot.ylim(ymin=-1.05, ymax=1.05)
		pyplot.title("Amplitude Contrast Fit (%.2f, %.2f, %.2f) CC=%.3f"%(conf1, conf2, conf3, crosscorr))
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

	if crosscorr < -0.6:
		print "likely 180 degree out of phase"
		apDisplay.printWarning("Bad angle translation: %.8f"%(amp_con))
		return None

	if fitconf < 0.1 and amp_con > 0.4:
		apDisplay.printWarning("Bad fit confidence %.3f, ac=%.8f"%(fitconf, amp_con))
		return None

	if crosscorr < 0.5:
		apDisplay.printWarning("Bad angle translation: %.8f"%(amp_con))
		return None

	if amp_con < 0.0:
		apDisplay.printWarning("amp contrast is negative (reduce defocus): %.4f"%(amp_con))
		#return None

	if amp_con > 0.6:
		apDisplay.printWarning("amp contrast is too large (increase defocus): %.8f"%(amp_con))
		#return None

	return amp_con

#===================================================
#===================================================
#===================================================
def refineCTFOneDimension(radial_array, amp_con, zavg, normPSD, cs, wavelength, weights=None, msg=True):
	"""
	take a 2D normalized PSB and refines all CTF parameters
	using a linear least squares

	all values in meters
	"""
	apDisplay.printColor("BEFORE ac=%.3f, zavg=%.3e"%(amp_con, zavg), "cyan")
	print cs, wavelength
	print "resolution limits %.2f <> %.2f"%(1.0e10/radial_array.max(), 1.0e10/radial_array.min())

	### convert parameters
	C = math.sin(math.asin(amp_con) - math.pi/4.)
	D = math.sqrt(1 - C**2)

	### create astigmatic gamma function
	radialsq_array = radial_array**2
	gamma_array = ( -0.5*math.pi * cs * wavelength**3 * radialsq_array**2
		+ math.pi * wavelength * radialsq_array * zavg )

	### create refinement vectors
	cosvec = numpy.cos(2*gamma_array) #C
	sinvec = numpy.sin(2*gamma_array) #D
	onevec = numpy.ones(radialsq_array.shape)
	dCTFdGamma_array = -2*C*sinvec + 2*D*cosvec
	zavgvec = wavelength*math.pi*radialsq_array * dCTFdGamma_array

	### create X data matrix and adjust
	X = numpy.array([cosvec, sinvec, zavgvec, onevec, radialsq_array]).transpose()

	# create weighted matrix
	if weights is None:
		# make an identity matrix for no weights
		weights = numpy.ones(normPSD.shape[0])

	# adjust y values
	yprime = (normPSD - normPSD.mean())
	yprime /= numpy.abs(yprime).max()

	## solve it
	beta = leastsq.totalLeastSquares(X, yprime, weights)
	if beta is None:
		beta = leastsq.numpyLeastSquares(X, yprime)
	del X, weights
	if beta is None:
		apDisplay.printWarning("Least squares failed")
		return None

	#translate the values
	C = beta[0]
	D = beta[1]
	dzavg = beta[2]
	constant = beta[3]
	sqterm = beta[4]
	print beta
	psi = 0.5*math.atan2(C,D)
	print "psi=", psi
	phi = psi + math.pi/4
	print "phi=", phi
	amp_con = math.sin(phi)

	if dzavg/zavg > 1:
		apDisplay.printWarning("Bad defocus change: %.4e --> %.4e"%(zavg, zavg+dzavg))
		return None

	zavg += dzavg

	print "AFTER ac=%.3f, zavg=%.3e"%(amp_con, zavg)

	apDisplay.printColor("AFTER ac=%.3f, zavg=%.3e"%(amp_con, zavg), "cyan")

	newGamma = ( -0.5*math.pi * cs * wavelength**3 * radialsq_array**2
		+ math.pi * wavelength * radialsq_array * zavg )

	fitctf1 = C*cosvec + D*sinvec
	fitctf1b = numpy.sin(2*gamma_array + 2*psi)
	fitctf2 = numpy.sin(2*newGamma + 2*psi)
	newB = math.sqrt(1 - amp_con**2)
	# need to do the y' = 2 y - 1
	adjctf1 = 2 * numpy.power(amp_con*numpy.cos(newGamma) + newB*numpy.sin(newGamma), 2) - 1

	crosscorr = scipy.stats.pearsonr(fitctf2, adjctf1)[0]

	if crosscorr < -0.6:
		print "likely 180 degree out of phase"
		apDisplay.printWarning("Bad angle translation: %.8f"%(amp_con))

	if msg is True:
		from matplotlib import pyplot
		pyplot.clf()
		yprime2 = yprime - constant - sqterm*radialsq_array
		yprime2 /= numpy.abs(yprime2).max()
		pyplot.plot(radialsq_array, yprime2, '.', color="gray")
		pyplot.plot(radialsq_array, yprime2, 'k-',)
		pyplot.plot(radialsq_array, fitctf1b, 'r--',)
		pyplot.plot(radialsq_array, fitctf2, 'g--',)
		pyplot.plot(radialsq_array, adjctf1, 'b--',)

		conf1 = scipy.stats.pearsonr(yprime2, fitctf1b)[0]
		conf2 = scipy.stats.pearsonr(yprime2, adjctf1)[0]
		conf3 = scipy.stats.pearsonr(yprime2, fitctf2)[0]

		#pyplot.ylim(ymin=-1.05, ymax=1.05)
		pyplot.title("CTF Refine 1D Fit (%.2f, %.2f, %.2f) CC=%.3f"%(conf1, conf2, conf3, crosscorr))
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

	if crosscorr < 0.5:
		apDisplay.printWarning("Bad angle translation: %.8f"%(amp_con))
		return None

	if zavg > 20e-6 or zavg < 0.1e-6:
		apDisplay.printWarning("Bad defocus change: %.4e --> %.4e"%(zavg-dzavg, zavg))
		return None

	if amp_con < 0.0:
		apDisplay.printWarning("amp contrast is negative (reduce defocus): %.4f"%(amp_con))
		#return None

	if amp_con > 0.6:
		apDisplay.printWarning("amp contrast is too large (increase defocus): %.8f"%(amp_con))
		#return None

	return amp_con, zavg


#===================================================
#===================================================
#===================================================
def refineCTF(radial_array, angle_array, 
	amp_con, z1, z2, angle_astig, 
	normPSD, cs, wavelength, refineFlags=(1,1,1,1), weights=None, msg=True):
	"""
	take a 2D normalized PSB and refines all CTF parameters
	using a linear least squares

	all values in meters
	"""
	print "BEFORE ac=%.3f, z1=%.3e, z2=%.3e, astig=%.1f"%(amp_con, z1, z2, angle_astig)
	print cs, wavelength
	print "resolution limits %.2f <> %.2f"%(1.0e10/radial_array.max(), 1.0e10/radial_array.min())

	### convert parameters
	C = math.sin(math.asin(amp_con) - math.pi/4.)
	D = math.sqrt(1 - C**2)
	zavg = (z1 + z2)/2.0
	zdiff = z2 - z1
	if abs(zdiff) < 1e-9:
		# this prevents singular matrices
		zdiff = 1e-9
	astigrad = math.radians(angle_astig)

	### create astigmatic gamma function
	radialsq_array = radial_array**2
	astigcos_array = numpy.cos(2.0*(angle_array - astigrad))
	defocus_array = zavg - zdiff/2.0 * astigcos_array
	gamma_array = ( -0.5*math.pi * cs * wavelength**3 * radialsq_array**2
		+ math.pi * wavelength * radialsq_array * defocus_array )
	del defocus_array, radial_array

	### create refinement vectors
	cosvec = numpy.cos(2*gamma_array) #C
	sinvec = numpy.sin(2*gamma_array) #D
	dCTFdGamma_array = -2*C*sinvec + 2*D*cosvec
	onevec = numpy.ones(radialsq_array.shape)
	zavgvec = wavelength*math.pi*radialsq_array * dCTFdGamma_array
	zdiffvec = -0.5*zavgvec * astigcos_array
	zastigvec = zavgvec * zdiff * numpy.sin(2.0*(angle_array- astigrad))
	del gamma_array, astigcos_array, dCTFdGamma_array

	### create X data matrix and adjust y values
	#X = numpy.array([cosvec, sinvec]).transpose()
	X = numpy.vstack([cosvec, sinvec])
	if refineFlags[0] == 1:
		X = numpy.vstack([X, zavgvec])
	if refineFlags[1] == 1:
		X = numpy.vstack([X, zdiffvec])
	if refineFlags[2] == 1:
		X = numpy.vstack([X, zastigvec])
	X = numpy.vstack([X, onevec, radialsq_array])
	X = X.transpose()
	del cosvec, sinvec, zavgvec, zdiffvec, zastigvec, angle_array

	# create weighted matrix
	if weights is None:
		# make an identity matrix for no weights
		weights = numpy.ones(normPSD.shape[0])

	# adjust y values
	yprime = 2 * normPSD - 1

	## solve it
	beta = leastsq.totalLeastSquares(X, yprime, weights)
	if beta is None:
		beta = leastsq.numpyLeastSquares(X, yprime)
	del X, weights
	if beta is None:
		apDisplay.printWarning("Least squares failed")
		return None

	#translate the values
	index = 0
	C = beta[index]
	index += 1
	D = beta[index]
	index += 1
	if refineFlags[0] == 1:
		dzavg = beta[index]
		print "dzavg", dzavg
		index += 1
	else:
		dzavg = 0
	if refineFlags[1] == 1:
		dzdiff = beta[index]
		index += 1
		print "dzdiff", dzdiff
	else:
		dzdiff = 0
	if refineFlags[2] == 1:
		dtheta = beta[index] % 2*math.pi
		index += 1
		print "dtheta", dtheta
	else:
		dtheta = 0
	constant = beta[index]
	index += 1
	sqterm = beta[index]
	index += 1
	if refineFlags[3] == 1:
		psi = 0.5*math.atan2(C,D)
		phi = psi + math.pi/4
		amp_con = math.sin(phi)

	zavg += dzavg
	zdiff += dzdiff
	if zdiff < 0:
		zdiff = 0

	z1 = zavg - zdiff/2
	z2 = zavg + zdiff/2.

	if refineFlags[2] == 1:
		astigrad += dtheta
		angle_astig = math.degrees(astigrad)

	print "AFTER ac=%.3f, z1=%.3e, z2=%.3e, astig=%.1f"%(amp_con, z1, z2, angle_astig)

	if msg is True:
		from matplotlib import pyplot
		args = numpy.argsort(radialsq_array)
		radialsq_array = radialsq_array[args]
		yprime = yprime[args]
		pyplot.clf()
		yprime2 = yprime - constant - sqterm*radialsq_array
		yprime2 /= numpy.abs(yprime2).max()
		newGamma = ( -0.5*math.pi * cs * wavelength**3 * radialsq_array**2
			+ math.pi * wavelength * radialsq_array * zavg )
		newB = math.sqrt(1 - amp_con**2)
		adjctf1 = 2 * numpy.power(amp_con*numpy.cos(newGamma) + newB*numpy.sin(newGamma), 2) - 1
		pyplot.plot(radialsq_array, yprime2, '.', color="gray")
		#pyplot.plot(radialsq_array, yprime2, 'k-',)
		pyplot.plot(radialsq_array, adjctf1, 'b--',)
		pyplot.title("CTF Refine 2D Fit")
		pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
			bottom=0.05, left=0.05, top=0.95, right=0.95, )
		pyplot.show()

	if amp_con < 0.0:
		apDisplay.printWarning("amp contrast is negative (reduce defocus): %.4f"%(amp_con))
		#return None

	if amp_con > 0.5:
		apDisplay.printWarning("amp contrast is too large (increase defocus): %.8f"%(amp_con))
		#return None

	return amp_con, z1, z2, angle_astig






