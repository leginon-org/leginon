#!/usr/bin/env python

import time
import math
import numpy
import scipy.stats
import scipy.ndimage
from appionlib import apDisplay
from appionlib.apCtf import genctf
from appionlib.apCtf import ctftools
from appionlib.apImage import onedimfilter

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

	if numpy.any(numpy.isnan(normPSD)):  #note does not work with 'is True'
		apDisplay.printError("All values NaN, normPSD")
	if numpy.any(numpy.isnan(ctfdata)):  #note does not work with 'is True'
		apDisplay.printError("All values NaN, ctfdata")

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
	xsqStep = (xsqSecond-xsqStart)*1.8

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
		print ("%.5f (1/%.3fA) -> %.5f (1/%.3fA) + %.5f"
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
			#apDisplay.printMsg("1/%.1fA\t%.3f"%(1.0/math.sqrt(xsq), conf))
			pass
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
	nancount = 0
	while xsq < xsqEnd:
		#for index in range(startindex, endindex):
		index = numpy.searchsorted(raddatasq, xsq)
		xsq = raddatasq[index]
		xsqLower = xsq - xsqStep/2.0
		xsqUpper = xsq + xsqStep/2.0
		ind1 = numpy.searchsorted(raddatasq, xsqLower)
		ind2 = numpy.searchsorted(raddatasq, xsqUpper)
		if abs(ind2 - ind1) < 4:
			#Fix for when indices are too close
			ind1 = ind2 - 4
			#never mind just stop
			xsq = xsqEnd
		### compare CTF to data
		subnormdata = numpy.copy(normPSD[ind1:ind2])
		subctfdata = numpy.copy(ctfdata[ind1:ind2])
		conf = scipy.stats.pearsonr(subnormdata, subctfdata)[0]
		### save data and increment
		if debug is True:
			#apDisplay.printMsg("[%d,%d/%d]: 1/%.3fA\t%.3f"%(ind1, ind2, len(ctfdata), 1.0/math.sqrt(xsq), conf))
			pass
		if math.isnan(conf):
			apDisplay.printWarning("NaN value found in loop, index=%d"%(index))
			nancount += 1
			continue
		if nancount > 4:
			apDisplay.printError("Too many NaN values found in loop, aborting")
		newraddata.append(math.sqrt(xsq))
		confs.append(conf)
		xsq += xsqStep/4.0
	if debug is True:
		print "getCorrelationProfile(): end main loop"

	confsArray = numpy.array(confs, dtype=numpy.float64)
	#confs[0:2] = confs[0:2].max()
	newraddata = numpy.array(newraddata, dtype=numpy.float64)
	#f = open("confdata.csv", "w")
	#f.write("[")
	#for val in confsArray:
	#	f.write("%.3f,"%(val))
	#f.write("]")
	#f.close()
	if numpy.any(numpy.isnan(confsArray)):  #note does not work with 'is True'
		apDisplay.printError("All values NaN, pre-filter")
	confs = onedimfilter.reflectTanhLowPassFilter(confsArray, 4, fuzzyEdge=3)
	if numpy.any(numpy.isnan(confsArray)):  #note does not work with 'is True'
		apDisplay.printError("All values NaN, post-tanh")
	confs = scipy.ndimage.gaussian_filter1d(confsArray, 2)
	if numpy.any(numpy.isnan(confsArray)):  #note does not work with 'is True'
		apDisplay.printError("All values NaN, post-gauss")
	return newraddata, confsArray


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
	if debug is True:
		apDisplay.printMsg("getResolutionFromConf: num points %d"%(len(confs)))
		apDisplay.printMsg("getResolutionFromConf: overall max %.3f"%(confs.max()))
		apDisplay.printMsg("getResolutionFromConf: overall min %.3f"%(confs.min()))
		print(numpy.around(confs[:15],3))
		apDisplay.printMsg("getResolutionFromConf: first points max %.3f"%(confs[:3].max()))
	if len(confs) < 3:
		apDisplay.printWarning("Res calc failed: Not enough points")
		return None
	if confs.max() < limit:
		apDisplay.printWarning("Res calc failed: All conf values below desired limit %.2f"
			%(limit))
		return None
	if numpy.median(confs[:3]) < limit:
		apDisplay.printWarning("Res calc failed: Initial conf below desired limit %.2f"
			%(limit))
		return None
	if numpy.any(numpy.isnan(confs)):  #note does not work with 'is True'
		apDisplay.printWarning("Res calc failed: All values NaN")
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
		else:
			apDisplay.printError("Res calc failed: How did we get here? %d: %.1f <> %.1f"
				%(i, yminus, y))
			return None
	# confs did not fall below limit
	res = 1.0/raddata.max()
	apDisplay.printWarning("Conf did not fall below %.2f, use max res of %.1fA"
		%(limit, res))
	return res

