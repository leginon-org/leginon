#!/usr/bin/env python

import time
import math
import numpy
import scipy.stats
import scipy.ndimage
from appionlib import apDisplay
from appionlib.apCtf import genctf
from appionlib.apCtf import ctftools

debug = False

#=======================
def getCorrelationProfile(raddata, normPSD, ctfdata, peaks, freq):
	"""
	raddata - x data in inverse Angstroms
	normPSD - powerspectra data, normalized to 0 and 1
	ctfdata - generated CTF function
	peaks - array of ctf peaks
	freq - frequency of the x data
	"""

	raddatasq = raddata**2

	### PART 0: create lists
	newraddata = []
	confs = []

	if len(peaks) == 0:
		return None, None	

	### PART 1: standard data points
	firstpeak = peaks[0]
	xsqStart = (firstpeak*freq)**2
	xsqEnd = raddatasq.max()
	## choice of step size, either:
	#(1) division of the whole area
	#numstep = 6.
	#xsqStep = (xsqEnd-xsqStart)/numstep
	#(2) 1 1/2 periods of the CTF
	if len(peaks) >= 2:
		secondpeak = peaks[1]
		xsqSecond = (secondpeak*freq)**2
	else:
		xsqSecond = xsqEnd
	xsqStep = (xsqSecond-xsqStart)*1.5

	### make sure we stay within step size
	startindex = numpy.searchsorted(raddatasq, xsqStart+xsqStep/2.0)
	endindex = numpy.searchsorted(raddatasq, xsqEnd-xsqStep/2.0)

	### PART 2: initial data points, best for large defocus
	if debug is True:
		print "getCorrelationProfile(): starting initial loop"
	xsqStartPre = (firstpeak*freq)**2
	if startindex >= len(raddatasq):
		apDisplay.printWarning("First peak of CTF is greater than FFT resolution")
		return None, None
	xsqEndPre = raddatasq[startindex]
	xsqStepPre = (xsqSecond-xsqStart)*0.5
	preindex = numpy.searchsorted(raddatasq, xsqStartPre)
	xsq = raddatasq[preindex]
	if debug is True:
		print ("%.5f (1/%.1fA) -> %.5f (1/%.1fA) + %.5f"
			%(xsqStartPre, 1.0/math.sqrt(xsqStartPre), 
			xsqEndPre, 1.0/math.sqrt(xsqEndPre), xsqStepPre))
	while xsq < xsqEndPre:
		#for index in range(startindex, endindex):
		index = numpy.searchsorted(raddatasq, xsq)
		xsq = raddatasq[index]
		xsqLower = xsq - xsqStepPre/2.0
		xsqUpper = xsq + xsqStepPre/2.0
		ind1 = numpy.searchsorted(raddatasq, xsqLower)
		ind2 = numpy.searchsorted(raddatasq, xsqUpper)
		### compare CTF to data
		conf = scipy.stats.pearsonr(normPSD[ind1:ind2], ctfdata[ind1:ind2])[0]
		### save data and increment
		if debug is True:
			apDisplay.printMsg("1/%.1fA\t%.3f"%(1.0/math.sqrt(xsq), conf))
		newraddata.append(math.sqrt(xsq))
		### add a sqrt bonus to early points in effort to prevent false positives
		confs.append(math.sqrt(abs(conf)))
		xsq += xsqStep/4.0
	if debug is True:
		print "getCorrelationProfile(): end initial loop"

	### PART 3: fill in the standard resolutions
	if debug is True:
		print "getCorrelationProfile(): starting main loop"
	if debug is True:
		print ("%.5f (1/%.1fA) -> %.5f (1/%.1fA) + %.5f"
			%(xsqStart, 1.0/math.sqrt(xsqStart), 
			xsqEnd, 1.0/math.sqrt(xsqEnd), xsqStep))
	xsq = raddatasq[startindex]
	while xsq < xsqEnd:
		#for index in range(startindex, endindex):
		index = numpy.searchsorted(raddatasq, xsq)
		xsq = raddatasq[index]
		xsqLower = xsq - xsqStep/2.0
		xsqUpper = xsq + xsqStep/2.0
		ind1 = numpy.searchsorted(raddatasq, xsqLower)
		ind2 = numpy.searchsorted(raddatasq, xsqUpper)
		### compare CTF to data
		conf = scipy.stats.pearsonr(normPSD[ind1:ind2], ctfdata[ind1:ind2])[0]

		### save data and increment
		if debug is True:
			apDisplay.printMsg("1/%.1fA\t%.3f"%(1.0/math.sqrt(xsq), conf))
		newraddata.append(math.sqrt(xsq))
		confs.append(conf)
		xsq += xsqStep/4.0
	if debug is True:
		print "getCorrelationProfile(): end main loop"

	confs = numpy.array(confs, dtype=numpy.float64)
	newraddata = numpy.array(newraddata, dtype=numpy.float64)
	confs = scipy.ndimage.gaussian_filter1d(confs, 2)

	return newraddata, confs


#==================
#==================
def getWeightsForXValues(raddata, newraddata, confs):
	"""
	raddata    - x data in inverse Angstroms
	newraddata - from getCorrelationProfile()
	confs      - from getCorrelationProfile()
	"""

	weights = numpy.interp(raddata, newraddata, confs, left=1e-7, right=1e-7)
	weights = numpy.where(weights < 0.0, 0.0, weights)
	firstpoint = numpy.searchsorted(raddata, newraddata[1])
	res5 = getResolutionFromConf(newraddata, confs, limit=0.5)
	if res5 is None:
		return None, 0, len(raddata)
	else:
		lastpoint = numpy.searchsorted(raddata, 1/res5)
	return weights, firstpoint, lastpoint


#==================
#==================
def getResolutionFromConf(raddata, confs, limit=0.5):
	"""
	should use more general apFourier.getResolution()
	"""
	if raddata is None or confs is None:
		return None
	lastx=0
	lasty=0
	x = 0
	if len(confs) < 3:
		apDisplay.printWarning("Res calc failed: Not enough points")
		return None
	if max(confs[0], confs[1], confs[2]) < limit:
		apDisplay.printWarning("Res calc failed: Initial conf below desired limit %.2f"
			%(limit))
		return None
	for i in range(1, raddata.shape[0]):
		x = raddata[i]
		y = confs[i]
		yminus = confs[i-1]
		if y > limit:
			#store values for later
			lastx = x
			lasty = y
		elif yminus > limit:
			# get difference
			diffy = lasty-y
			# get distance from limit
			dist = (limit-y) / diffy
			# get interpolated spatial freq
			interpx = x - dist*(x-lastx)
			# convert to Angstroms
			res = 1.0/interpx
			return res
	# confs did not fall below limit
	res = 1.0/raddata.max()
	apDisplay.printWarning("Conf did not fall below %.2f, use max res of %.1fA"
		%(limit, res))
	return res

