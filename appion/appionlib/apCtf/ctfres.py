#!/usr/bin/env python

import time
import math
import numpy
import scipy.stats
import scipy.ndimage
from appionlib import apDisplay
from appionlib.apCtf import genctf
from appionlib.apCtf import ctftools

debug = True

	

#=======================
def getCorrelationProfile(raddata, rotdata, freq, ctfvalues):
		"""
		raddata - x data in inverse Angstroms
		rotdata - powerspectra data, normalized to 0 and 1
		freq - frequency of the x data
		ctfvalues:
			apix - real space pixelsize in Angstroms
			defocus2 - defocus value to use in meters, underfocus is positive
			volts - potential of the microscope in volts
			cs - spherical abberation of microscope in meters
			amplitude_contrast - amplitude contrast of ctf profile
		"""

		if debug is True:
			from matplotlib import pyplot

		raddatasq = raddata**2

		### get the peaks
		if debug is True:
			numzeros = 14
		else:
			numzeros = 2
		numcols = int(0.5/(freq*ctfvalues['apix']))
		peakradii = ctftools.getCtfExtrema(ctfvalues['defocus2'], ctfvalues['apix']*1e-10, 
			ctfvalues['cs'], ctfvalues['volts'], ctfvalues['amplitude_contrast'], 
			cols=numcols, numzeros=numzeros, zerotype="peaks")
		if debug is True:
			valleyradii = ctftools.getCtfExtrema(ctfvalues['defocus2'], ctfvalues['apix']*1e-10, 
				ctfvalues['cs'], ctfvalues['volts'], ctfvalues['amplitude_contrast'], 
				cols=numcols, numzeros=numzeros, zerotype="valleys")
		firstpeak = peakradii[0]
		firstpeakindex = numpy.searchsorted(raddata, firstpeak*freq)

		### get the ctf
		genctfdata = genctf.generateCTF1d(raddata*1e10, focus=ctfvalues['defocus2'], cs=ctfvalues['cs'],
			pixelsize=ctfvalues['apix']*1e-10, volts=ctfvalues['volts'], ampconst=ctfvalues['amplitude_contrast'])
		genctfdata = genctfdata**2

		## divide the data into 8 section (by x^2 not x) and calculate the correlation correficient for each
		xsqStart = (firstpeak*freq)**2
		xsqEnd = raddatasq.max()
		## choice of step size, either:
		#(1) division of the whole area
		#numstep = 6.
		#xsqStep = (xsqEnd-xsqStart)/numstep
		#(2) 1 1/2 periods of the CTF
		secondpeak = peakradii[1]
		xsqSecond = (secondpeak*freq)**2
		xsqStep = (xsqSecond-xsqStart)*1.5

		print "1/%.1fA <-> 1/%.1fA"%(1/math.sqrt(xsqStart), 1/math.sqrt(xsqEnd))

		### make sure we stay within step size
		startindex = numpy.searchsorted(raddatasq, xsqStart+xsqStep/2.0)
		endindex = numpy.searchsorted(raddatasq, xsqEnd-xsqStep/2.0)

		## create empty array with zeros
		confs = -numpy.zeros(raddatasq.shape)
		## make all points before checking one
		confs[:startindex] = 1.0

		## now fill in the resolutions
		for index in range(startindex, endindex):
			xsq = raddatasq[index]
			xsqLower = xsq - xsqStep/2.0
			xsqUpper = xsq + xsqStep/2.0
			ind1 = numpy.searchsorted(raddatasq, xsqLower)
			ind2 = numpy.searchsorted(raddatasq, xsqUpper)
			### compare CTF to data
			conf = scipy.stats.pearsonr(rotdata[ind1:ind2], genctfdata[ind1:ind2])[0]
			confs[index] = conf

		confs = scipy.ndimage.gaussian_filter1d(confs, 2)

		res5 = getResolutionFromConf(raddata, confs, limit=0.5)
		res8 = getResolutionFromConf(raddata, confs, limit=0.8)

		if debug is True:
			pyplot.clf()
			#draw vertical lines
			for radii in peakradii:
				index = numpy.searchsorted(raddata, radii*freq)	
				if index > raddata.shape[0] - 1:
					break
				pyplot.axvline(x=raddatasq[index], linewidth=1, color="cyan", alpha=0.5)
			for radii in valleyradii:
				index = numpy.searchsorted(raddata, radii*freq)
				if index > raddata.shape[0] - 1:
					break
				pyplot.axvline(x=raddatasq[index], linewidth=1, color="yellow", alpha=0.5)
			### raw powerspectra data
			pyplot.plot(raddatasq[firstpeakindex:], rotdata[firstpeakindex:], 'x', color="red", alpha=0.9, markersize=10)
			pyplot.plot(raddatasq[firstpeakindex:], rotdata[firstpeakindex:], '-', color="red", alpha=0.5, linewidth=2)
			### ctf fit data
			pyplot.plot(raddatasq[firstpeakindex:], genctfdata[firstpeakindex:], '.', color="black", alpha=0.9, markersize=10)
			pyplot.plot(raddatasq[firstpeakindex:], genctfdata[firstpeakindex:], '-', color="black", alpha=0.5, linewidth=2)
			### confidence profile
			pyplot.plot(raddatasq[startindex:endindex], confs[startindex:endindex], '-', color="blue", alpha=0.9, linewidth=2)
			xmin = raddatasq[firstpeakindex-1]
			xmax = raddatasq.max()
			pyplot.xlim(xmin=xmin, xmax=raddatasq.max())
			pyplot.ylim(ymin=-0.05, ymax=1.05)

			locs, labels = pyplot.xticks()
			newlocs = []
			newlabels = []
			for loc in locs:
				if loc < xmin:
					continue
				res = round(1.0/math.sqrt(loc),1)
				label = "1/%.1fA"%(res)
				newloc = 1.0/res**2
				newlocs.append(newloc)
				newlabels.append(label)
			pyplot.xticks(newlocs, newlabels)

			pyplot.axvline(x=1/res8**2, linewidth=2, color="gold")
			pyplot.axvline(x=1/res5**2, linewidth=2, color="red")

			pyplot.title("Resolution values of %.1fA at 0.8 and %.1fA at 0.5"%(res8,res5))
			pyplot.show()
			apDisplay.printColor("Resolution values of %.4fA at 0.8 and %.4fA at 0.5"%(res8,res5), "cyan")

		return confs


#==================
#==================
def getResolutionFromConf(raddata, confs, limit=0.5):
	"""
	should use more general apFourier.getResolution()
	"""
	lastx=0
	lasty=0
	x = 0
	for i in range(raddata.shape[0]):
		x = raddata[i]
		y = confs[i]
		if y > limit:
			#store values for later
			lastx = x
			lasty = y
		else:
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
	apDisplay.printWarning("Failed to determine resolution")
	res = 1.0/raddata.max()
	return res

