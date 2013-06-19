#!/usr/bin/env python

import math
import time
import numpy
import scipy.stats
from matplotlib import pyplot
from appionlib import apDisplay
from appionlib.apImage import imagestat
from appionlib.apCtf import ctftools, genctf

#===================================================
#===================================================
#===================================================
def refineAmplitudeContrast(radial_array, defocus, normPSD, cs, wavelength):
	"""
	takes elliptical average data and fits it to the equation
	A cos(x) + B sin(x)
	"""

	print "resolution limits %.2f <> %.2f"%(1.0e10/radial_array.max(), 1.0e10/radial_array.min())

	# create X matrix
	radialsq = radial_array**2
	print 1.0/radial_array[-1], wavelength, defocus, cs
	gamma = ( -0.5 * math.pi * cs * wavelength**3 * radialsq**2
		+ math.pi * wavelength * radialsq * defocus )
	cosvec = numpy.cos(2*gamma) #C
	sinvec = numpy.sin(2*gamma) #D
	X = numpy.array([cosvec, sinvec]).transpose()
	#del cosvec, sinvec, gamma

	print "gamma"
	imagestat.printImageInfo(gamma)

	# adjust y values
	yprime = 2 * normPSD - 1

	# QR decomposition
	Q, R = numpy.linalg.qr(X)
	if numpy.linalg.det(R) == 0:
		apDisplay.printWarning("Singular matrix in calculation")
		return None
	QT = numpy.transpose(Q)
	Rinv = numpy.linalg.inv(R)
	del X

	#do the least squares
	beta = numpy.dot(numpy.dot(Rinv, QT), yprime)
	C = beta[0]
	D = beta[1]
	print beta, radial_array.shape
	psi = 0.5*math.atan2(C,D)
	phi = psi + math.pi/4
	if phi < 0:
		phi += math.pi
	amplitude_contrast = math.sin(phi)

	apDisplay.printColor("amplitude contrast = %.8f"%(amplitude_contrast), "cyan")

	fitctf1 = C*cosvec + D*sinvec
	fitctf2 = numpy.sin(2*gamma + 2*psi)
	newB = math.sqrt(1 - amplitude_contrast**2)
	# need to do the y' = 2 y - 1
	adjctf1 = 2 * numpy.power(amplitude_contrast*numpy.cos(gamma) + newB*numpy.sin(gamma), 2) - 1
	#adjctf2 = 2 * numpy.power(numpy.sin(gamma + math.asin(amplitude_contrast)), 2) - 1

	pyplot.clf()
	pyplot.plot(radialsq, yprime, '.', color="gray")
	pyplot.plot(radialsq, yprime, 'k-',)
	pyplot.plot(radialsq, fitctf1, 'r--',)
	pyplot.plot(radialsq, fitctf2, 'g--',)
	pyplot.plot(radialsq, adjctf1, 'b--',)
	conf1 = scipy.stats.pearsonr(yprime, fitctf1)[0]
	conf2 = scipy.stats.pearsonr(yprime, adjctf1)[0]
	conf3 = scipy.stats.pearsonr(yprime, fitctf2)[0]

	print "conf %.4f, %.4f, %.4f"%(conf1, conf2, conf3)

	pyplot.ylim(ymin=-1.05, ymax=1.05)
	pyplot.title("Amplitude Contrast Fit")
	pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
		bottom=0.05, left=0.05, top=0.95, right=0.95, )
	pyplot.show()

	if amplitude_contrast > 0.6 or amplitude_contrast < 0.0:
		apDisplay.printWarning("Fit out of range, bad amp contrast: %.8f"%(amplitude_contrast))
		return None

	return amplitude_contrast

#===================================================
#===================================================
#===================================================
def refineCTF(radial_array, angle_array, 
	amp_cont, z1, z2, angle_astig, 
	normPSD, cs, wavelength):
	"""
	take a 2D normalized PSB and refines all CTF parameters
	using a linear least squares

	all values in meters
	"""
	print "BEFORE ac=%.3f, z1=%.3e, z2=%.3e, astig=%.1f"%(amp_cont, z1, z2, angle_astig)
	print cs, wavelength
	print "resolution limits %.2f <> %.2f"%(1.0e10/radial_array.max(), 1.0e10/radial_array.min())

	### convert parameters
	C = math.sin(math.asin(amp_cont) - math.pi/4.)
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
	zavgvec = wavelength*math.pi*radialsq_array * dCTFdGamma_array
	zdiffvec = -0.5*zavgvec * astigcos_array
	zastigvec = zavgvec * zdiff * numpy.sin(2.0*(angle_array- astigrad))
	del gamma_array, astigcos_array, dCTFdGamma_array

	### create X data matrix and adjust y values
	#X = numpy.array([cosvec, sinvec]).transpose()
	X = numpy.array([cosvec, sinvec, zavgvec, zdiffvec, zastigvec]).transpose()
	yprime = 2 * normPSD - 1
	del cosvec, sinvec, zavgvec, zdiffvec, zastigvec, normPSD, angle_array

	### QR decompostion
	Q, R = numpy.linalg.qr(X)
	del X
	if numpy.linalg.det(R) == 0:
		apDisplay.printWarning("Singular matrix in calculation")
		return None
	QT = numpy.transpose(Q)
	Rinv = numpy.linalg.inv(R)
	del Q, R

	#do the least squares
	beta = numpy.dot(numpy.dot(Rinv, QT), yprime)
	C = beta[0]
	D = beta[1]
	dzavg = beta[2]
	dzdiff = beta[3]
	dtheta = beta[4]
	print beta
	psi = 0.5*math.atan2(C,D)
	phi = psi + math.pi/4
	if phi < 0:
		phi += math.pi
	amp_cont = math.sin(phi)
	zavg += dzavg
	zdiff += dzdiff
	if zdiff < 0:
		zdiff = 0
	astigrad += dtheta
	angle_astig = math.degrees(astigrad)
	z1 = zavg - zdiff/2
	z2 = zavg + zdiff/2.

	print "AFTER ac=%.3f, z1=%.3e, z2=%.3e, astig=%.1f"%(amp_cont, z1, z2, angle_astig)

	if amp_cont > 0.6 or amp_cont < 0.0:
		apDisplay.printWarning("Fit out of range, bad amp contrast: %.8f"%(amp_cont))
		return None

	return amp_cont, z1, z2, angle_astig
