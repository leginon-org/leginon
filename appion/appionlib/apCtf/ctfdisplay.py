#!/usr/bin/env python

import os
import sys
import math
import copy
import numpy
import time
import random
from pyami import ellipse
from pyami import mrc
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib.apImage import imagefile
from appionlib.apImage import imagefilter
from matplotlib import use
use('Agg')
from matplotlib import pyplot
from appionlib.apCtf import ctfnoise
from appionlib.apCtf import ctftools
from appionlib.apCtf import ctfdb
from appionlib.apCtf import genctf
from appionlib.apCtf import ctfres
from PIL import Image
from PIL import ImageDraw
from scipy import ndimage
import scipy.stats

class CtfDisplay(object):
	#====================
	#====================
	def __init__(self):
		### global params that do NOT change with image
		self.ringwidth = 1.0
		self.debug = False
		self.outerAngstrom1D = 3.0
		# plotlimit2DAngstrom trims the power spectrum generated
		#from self.outerAngstrom1D limit for the 2D plot
		self.plotlimit2DAngstrom = 5.0
		## num of sections to divide the 1D spectrum into
		## initially it was 3 sections to 5 A (or 0.2 A-1)
		## for going to 3 A (0.33 A-1) should be 5 sections
		self.numSections = int(math.ceil(15.0/self.outerAngstrom1D))
		### the following variables control how the section are divided up
		self.sectionFactor = 3
		self.overlapFactor = 2
		return

	#====================
	#====================
	def funcrad(self, r, rdata=None, zdata=None):
		return numpy.interp(r, rdata, zdata)


	#====================
	#====================
	def extremaToIndex(self, requestVal, extremaList, raddata):
		"""
		takes a peak or valley point and converts to a raddata index
		"""
		extremaIndex = numpy.searchsorted(extremaList, requestVal)
		extremaIndex = numpy.clip(extremaIndex, 1, len(extremaList)-1)
		left = extremaList[extremaIndex-1]
		right = extremaList[extremaIndex]
		extremaIndex -= requestVal - left < right - requestVal
		extremaVal = extremaList[int(extremaIndex)]

		trimVal = self.trimfreq*extremaVal
		index = numpy.searchsorted(raddata, trimVal)
		index = numpy.clip(index, 1, len(raddata)-1)
		left = raddata[index-1]
		right = raddata[index]
		index -= trimVal - left < right - trimVal

		if self.debug is True:
			print "extremaToIndex Debug"
			print "... requestVal = %.8f"%(requestVal)
			print "... extremaIndex = %d"%(extremaIndex)
			print "... extremaList[extremaIndex-1] = %.8f"%(extremaList[int(extremaIndex)-1])			
			print "... extremaVal = extremaList[extremaIndex] = %.8f"%(extremaVal)
			try:
				print "... extremaList[extremaIndex+1] = %.8f"%(extremaList[int(extremaIndex)+1])
			except IndexError:
				pass
			#print "... extremaList = ", numpy.around(extremaList, 2)
			print "... trimFreq = %.8f"%(self.trimfreq)
			print "... extremaVal*trimFreq = %.4f"%(self.trimfreq*extremaVal)
			print "... index = %d"%(index)
			#print "... raddata = ", numpy.around(raddata, 2)
			print "... raddata[index-1] = %.4f"%(raddata[index-1])			
			print "... raddata[index] = %.4f"%(raddata[index])
			try:
				print "... raddata[index+1] = %.4f"%(raddata[index+1])
			except IndexError:
				pass
			
		return index

	#====================
	#====================
	def normalizeCtf(self, zdata2d, twod=True):
		"""
		inner cut radius - radius for number of pixels to clip in the center of image
		"""
		### 
		### PART 1: SETUP PARAMETERS AND ELLIPTICAL AVERAGE
		###
		apDisplay.printColor("PART 1: SETUP PARAMETERS AND ELLIPTICAL AVERAGE", "magenta")
		numSections=self.numSections
		
		meandefocus = math.sqrt(self.defocus1*self.defocus2)
		if meandefocus < 0.6e-6:
			self.ringwidth = 3.0
		elif meandefocus < 1.0e-6:
			self.ringwidth = 2.0
		elif meandefocus > 5.0e-6:
			self.ringwidth = 0.5

		### get all peak (not valley)
		peak = ctftools.getCtfExtrema(meandefocus, self.trimfreq*1e10, self.cs, self.volts, 
			self.ampcontrast, numzeros=250, zerotype="peak")
		apDisplay.printMsg("Number of available peaks is %d"%(len(peak)))
		if len(peak) < 6:
			apDisplay.printWarning("Too few peaks to work with, probably bad defocus estimate")
			return None
		firstpeak = peak[0]
		peakradii = numpy.array(peak, dtype=numpy.float64)*self.trimfreq
		### get all valley (not peak)
		valley = ctftools.getCtfExtrema(meandefocus, self.trimfreq*1e10, self.cs, self.volts, 
			self.ampcontrast, numzeros=250, zerotype="valley")
		valleyradii = numpy.array(valley, dtype=numpy.float64)*self.trimfreq

		### do the elliptical average
		if self.ellipratio is None:
			return None
		pixelrdata, rotdata = ctftools.ellipticalAverage(zdata2d, self.ellipratio, self.angle,
			self.ringwidth, firstpeak, full=False)
		raddata = pixelrdata*self.trimfreq

		if self.debug is True:
			print "Elliptical CTF limits %.1f A -->> %.1fA"%(1./raddata.min(), 1./raddata.max())

		apDisplay.printMsg("Determine and subtract noise model")
		CtfNoise = ctfnoise.CtfNoise()

		### 
		### PART 1B: NUMBER OF SECTIONS
		### 
		apDisplay.printColor("PART 2: BACKGROUND NOISE SUBTRACTION", "magenta")

		### split the function up into sections
		firstvalley = valley[0]
		firstvalleyindex = self.extremaToIndex(firstvalley, valley, raddata)
		noiseNumPoints = len(raddata) - firstvalleyindex
		# require at least 10 points past first peak of CTF to perform estimation
		maxSections = int(math.floor(noiseNumPoints/12.))
		if numSections > maxSections:
			apDisplay.printWarning("Not enough points (%d) for %d sections, reducing to %d sections"
				%(noiseNumPoints, numSections, maxSections))
			numSections = maxSections
		if numSections < 2:
			apDisplay.printWarning("Too few points to work with, probably bad defocus estimate")
			return None
		minPoints = 4 * numSections
		if noiseNumPoints < minPoints:
			apDisplay.printWarning("Not enough points past first peak (n=%d < %d) to do background subtraction"
				%(noiseNumPoints, minPoints))
			return None
		# for 3 sections, we take 10 parts, section1=parts1-4; section2=parts3-7; section3=parts6-10;
		# scale this so each section is always 4 parts, remove the ends.
	
		noiseStartIndexes = []
		noiseEndIndexes = []
		numParts = self.sectionFactor*numSections + self.overlapFactor
		for section in range(numSections):
			partStart = self.sectionFactor*section
			start = firstvalley + noiseNumPoints*partStart/float(numParts)
			startIndex = self.extremaToIndex(start, valley, raddata)
			noiseStartIndexes.append(startIndex)
			partEnd = partStart + (self.sectionFactor+self.overlapFactor)
			end = firstvalley + noiseNumPoints*partEnd/float(numParts)
			endIndex = self.extremaToIndex(end, valley, raddata)
			if endIndex - startIndex < 4:
				apDisplay.printWarning("Not enough points (%d) in section %d to do background subtraction"
					%(endIndex - startIndex, section))
				return None
			noiseStartIndexes.append(startIndex)
			noiseEndIndexes.append(endIndex)
			
		mergeIndexes = copy.copy(noiseStartIndexes)
		mergeIndexes.extend(noiseEndIndexes)
		mergeIndexes.sort()
		if self.debug is True:
			print noiseStartIndexes
			print noiseEndIndexes
			print "Noise mergeIndexes", mergeIndexes	
		### 
		### PART 2: BACKGROUND NOISE SUBTRACTION
		### 

		#do like a minimum filter
		fitvalleydata = ctfnoise.peakExtender(raddata, rotdata, valleyradii, "below")
		fitvalleydata = (rotdata+3*fitvalleydata)/4.0
		fitvalleydata = ndimage.minimum_filter(fitvalleydata, 3)

		### fit function below log(CTF), i.e., noise model	
		noiseFitParamList = []
		noiseDataList = []
		for section in range(numSections):
			if self.debug is True:
				apDisplay.printMsg("fitting noise section %d of %d"%(section+1, numSections))
			startIndex = noiseStartIndexes[section]
			endIndex = noiseEndIndexes[section]
			tfit = time.time()
			noisefitparams = CtfNoise.modelCTFNoise(raddata[startIndex:endIndex],
				fitvalleydata[startIndex:endIndex], "below")
			noiseFitParamList.append(noisefitparams)
			noisedata = CtfNoise.noiseModel(noisefitparams, raddata)
			if self.debug is True:
				apDisplay.printMsg("finished in %s"%(apDisplay.timeString(time.time()-tfit)))
			noiseDataList.append(noisedata)

		## debug only
		if self.debug is True:
			startIndex = noiseStartIndexes[0]
			endIndex = noiseEndIndexes[-1]
			singlenoisefitparams = CtfNoise.modelCTFNoise(raddata[startIndex:endIndex],
				fitvalleydata[startIndex:endIndex], "below")
			singlenoisedata = CtfNoise.noiseModel(singlenoisefitparams, raddata)

		#print noiseStartIndexes
		#print noiseEndIndexes
		## merge data
		# add crappy "fit" points before the actual fitting, these will be ignored later
		mergedata = noiseDataList[0][:noiseStartIndexes[0]]
		for section in range(numSections-1):
			insertStart = mergeIndexes[section*2]
			insertEnd = mergeIndexes[section*2+1]
			overlapStart = insertEnd
			overlapEnd = mergeIndexes[section*2+2]
			if self.debug is True:
				print "section %d mergedata"%(section), mergedata.shape
			scale = numpy.arange(overlapEnd-overlapStart, dtype=numpy.float32)
			scale /= scale.max()
			scale *= math.pi/2.0
			scale = numpy.cos(scale)**2
			if self.debug is True:
				print "\tinsert from %d to %d (%d)"%(insertStart,insertEnd, insertEnd-insertStart)
				print "\toverlap from %d to %d (%d)"%(overlapStart,overlapEnd, overlapEnd-overlapStart)
			overlapData = (noiseDataList[section][overlapStart:overlapEnd]*(scale) 
				+ noiseDataList[section+1][overlapStart:overlapEnd]*(1.0-scale))
			mergedata = numpy.hstack((
				mergedata,
				noiseDataList[section][insertStart:insertEnd],
				overlapData,
				))
		if self.debug is True:
			print "section %d mergedata"%(section+1), mergedata.shape	
		### add last section
		startIndex = noiseEndIndexes[-2]		 
		endIndex = len(rotdata)
		if self.debug is True:
			print "\t", mergedata.shape, endIndex-startIndex
		mergedata = numpy.hstack((mergedata, noiseDataList[-1][startIndex:endIndex]))
		if self.debug is True:
			print "section %d mergedata"%(section+2), mergedata.shape	

		noisedata = mergedata

		### DO THE SUBTRACTION

		#print "rotdata", rotdata.shape, "mergedata", noisedata.shape
		normexprotdata = numpy.exp(rotdata) - numpy.exp(noisedata)

		### CUT OUT ANY NEGATIVE VALUES FOR DISPLAY AND FITTING PURPOSES ONLY
		minval = -1
		mindata = ndimage.maximum_filter(normexprotdata, 2)
		count = 0
		while minval < 3 and count < 10:
			count += 1
			mindata = ndimage.maximum_filter(mindata, 2)
			minval = mindata.min()
			if self.debug is True:
				apDisplay.printMsg("Minimum value for normalization: %.3f"%(minval))
		if minval < 3:
			minval = 3
		normlogrotdata = numpy.log(numpy.where(normexprotdata<minval, minval, normexprotdata))
		if numpy.isnan(normlogrotdata).any() is True:
			apDisplay.printError("Error in log normalization of CTF data")

		### 
		### PART 3: ENVELOPE NORMALIZATION
		### 
		apDisplay.printColor("PART 3: ENVELOPE NORMALIZATION", "magenta")

		### split the function up into sections
		firstpeakindex = self.extremaToIndex(firstpeak, peak, raddata)
		fpi = firstpeakindex

		envelopNumPoints = len(raddata) - firstpeakindex

		#convert back to exponential data for fitting...
		expnormlogrotdata = numpy.exp(normlogrotdata)
		#do like a maximum filter
		peakdata = ctfnoise.peakExtender(raddata, expnormlogrotdata, peakradii, "above")
		fitpeakdata = (3*peakdata+expnormlogrotdata)/4.0
		fitpeakdata = ndimage.maximum_filter(fitpeakdata, 3)
		# for some reason, CtfModel is really slow on numbers too high
		maxvalue = fitpeakdata[fpi:].max()/10
		if self.debug is True:
			print "max value", maxvalue
		fitpeakdata /= maxvalue
		#fitpeakdata = ctfnoise.peakExtender(raddata, expnormlogrotdata, peakradii, "above")

		envelopStartIndexes = []
		envelopEndIndexes = []
		numParts = self.sectionFactor*numSections + self.overlapFactor
		for section in range(numSections):
			partStart = self.sectionFactor*section
			start = firstpeak + envelopNumPoints*partStart/float(numParts)
			startIndex = self.extremaToIndex(start, peak, raddata)
			partEnd = partStart + (self.sectionFactor+self.overlapFactor)			
			end = firstpeak + envelopNumPoints*partEnd/float(numParts)
			endIndex = self.extremaToIndex(end, peak, raddata)
			if endIndex - startIndex < 4:
				apDisplay.printWarning("Not enough points (%d) in section %d to do background subtraction"
					%(endIndex - startIndex, section))
				return None
			envelopStartIndexes.append(startIndex)
			envelopEndIndexes.append(endIndex)
		mergeIndexes = copy.copy(envelopStartIndexes)
		mergeIndexes.extend(envelopEndIndexes)
		mergeIndexes.sort()		
		if self.debug is True:
			print envelopStartIndexes
			print envelopEndIndexes
			print "Envelop mergeIndexes", mergeIndexes

		### fit the envelope in each section
		envelopFitParamList = []
		envelopDataList = []
		for section in range(numSections):
			if self.debug is True:
				apDisplay.printMsg("fitting envelop section %d of %d"%(section+1, numSections))			
			startIndex = envelopStartIndexes[section]
			endIndex = envelopEndIndexes[section]
			tfit = time.time()
			envelopfitparams = CtfNoise.modelCTFNoise(raddata[startIndex:endIndex],
				fitpeakdata[startIndex:endIndex], "above")
			envelopFitParamList.append(envelopfitparams)
			envelopdata = CtfNoise.noiseModel(envelopfitparams, raddata)
			envelopdata *= maxvalue
			if self.debug is True:
				apDisplay.printMsg("finished in %s"%(apDisplay.timeString(time.time()-tfit)))			
			envelopDataList.append(envelopdata)
		fitpeakdata *= maxvalue

		## merge data
		mergedata = envelopDataList[0][:envelopStartIndexes[0]]
		for section in range(numSections-1):
			insertStart = mergeIndexes[section*2]
			insertEnd = mergeIndexes[section*2+1]
			overlapStart = insertEnd
			overlapEnd = mergeIndexes[section*2+2]
			if self.debug is True:
				print "section %d mergedata"%(section), mergedata.shape
			scale = numpy.arange(overlapEnd-overlapStart, dtype=numpy.float32)
			scale /= scale.max()
			scale *= math.pi/2.0
			scale = numpy.cos(scale)**2
			if self.debug is True:
				print "\tinsert from %d to %d (%d)"%(insertStart,insertEnd, insertEnd-insertStart)
				print "\toverlap from %d to %d (%d)"%(overlapStart,overlapEnd, overlapEnd-overlapStart)
			overlapData = (envelopDataList[section][overlapStart:overlapEnd]*(scale) 
				+ envelopDataList[section+1][overlapStart:overlapEnd]*(1.0-scale))
			mergedata = numpy.hstack((
				mergedata,
				envelopDataList[section][insertStart:insertEnd],
				overlapData,
				))
		if self.debug is True:
			print "section %d mergedata"%(section+1), mergedata.shape	
		### add last section
		startIndex = envelopEndIndexes[-2]		 
		endIndex = len(normexprotdata)
		if self.debug is True:
			print "\t", mergedata.shape, endIndex-startIndex
		mergedata = numpy.hstack((mergedata, envelopDataList[-1][startIndex:endIndex]))
		if self.debug is True:
			print "section %d mergedata"%(section+2), mergedata.shape

		envelopdata = mergedata

		try:
			normnormexprotdata = normexprotdata / envelopdata
		except ValueError:
			print "raise ValueError"			
			print len(normexprotdata), len(envelopdata)
			sys.exit(1)

		### 
		### PART 4: PEAK EXTENSION
		### 
		apDisplay.printColor("PART 4: PEAK EXTENSION", "magenta")

		### Subtract fit valley locations
		valleydata = ctfnoise.peakExtender(raddata, normnormexprotdata, valleyradii, "below")
		valleydata = ndimage.gaussian_filter1d(valleydata, 1)
		normvalleydata = normnormexprotdata - valleydata

		### Normalize fit peak locations
		peakdata = ctfnoise.peakExtender(raddata, normvalleydata, peakradii, "above")
		peakdata = ndimage.gaussian_filter1d(peakdata, 1)
		normpeakdata = normvalleydata / peakdata

		### 
		### PART 5: CTF FIT AND CONFIDENCE
		### 
		apDisplay.printColor("PART 5: CTF FIT AND CONFIDENCE", "magenta")

		### everything in mks units, because rdata is 1/A multiply be 1e10 to get 1/m
		ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=meandefocus, cs=self.cs,
			volts=self.volts, ampconst=self.ampcontrast, failParams=False)
		#ctffitdata2 = genctf.generateCTF1dACE2(raddata*1e10, focus=meandefocus, cs=self.cs,
		#	volts=self.volts, ampconst=self.ampcontrast, failParams=False)
		overctffitdata = genctf.generateCTF1d(raddata*1e10, focus=meandefocus, cs=self.cs,
			volts=self.volts, ampconst=self.ampcontrast, failParams=False, overfocus=True)

		ind30 = numpy.searchsorted(raddata, 1/30.)
		ind10 = numpy.searchsorted(raddata, 1/10.)
		self.conf3010 = scipy.stats.pearsonr(normpeakdata[ind30:ind10], ctffitdata[ind30:ind10])[0]
		self.overconf3010 = scipy.stats.pearsonr(normpeakdata[ind30:ind10], overctffitdata[ind30:ind10])[0]
		apDisplay.printColor("1/30A - 1/10A confidence is %.3f (overfocus %.3f)"%(self.conf3010, self.overconf3010), "green")
		if self.overconf3010 > self.conf3010*1.1:
			apDisplay.printWarning("Image is possibly over-focused")

		ind5peak1 = numpy.searchsorted(raddata, peakradii[0])
		ind5peak2 = numpy.searchsorted(raddata, peakradii[5])
		self.conf5peak = scipy.stats.pearsonr(normpeakdata[ind5peak1:ind5peak2], ctffitdata[ind5peak1:ind5peak2])[0]
		self.overconf5peak = scipy.stats.pearsonr(normpeakdata[ind5peak1:ind5peak2], overctffitdata[ind5peak1:ind5peak2])[0]
		apDisplay.printColor("5 peak confidence is %.3f (overfocus %.3f)"%(self.conf5peak, self.overconf5peak), "green")
		if self.overconf5peak > self.conf5peak*1.1:
			apDisplay.printWarning("Image is possibly over-focused")

		### 
		### PART 6: CTF RESOLUTION LIMITS
		### 
		apDisplay.printColor("PART 6: CTF RESOLUTION LIMITS", "magenta")

		confraddata, confdata = ctfres.getCorrelationProfile(raddata, 
			normpeakdata, ctffitdata, peak, self.trimfreq)
		overconfraddata, overconfdata = ctfres.getCorrelationProfile(raddata, 
			normpeakdata, overctffitdata, peak, self.trimfreq)

		self.res80 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.8)
		if self.res80 is None:
			self.res80 = 100.0
		self.overres80 = ctfres.getResolutionFromConf(overconfraddata, overconfdata, limit=0.8)
		if self.overres80 is None:
			self.overres80 = 100.0
		self.res50 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.5)
		if self.res50 is None:
			self.res50 = 100.0
		self.overres50 = ctfres.getResolutionFromConf(overconfraddata, overconfdata, limit=0.5)
		if self.overres50 is None:
			self.overres50 = 100.0

		apDisplay.printColor("Resolution limit is %.2f at 0.8 and %.2f at 0.5"
			%(self.res80, self.res50), "green")

		### 
		### PART 7: MAKE 1D PLOT SUMMARY FIGURE
		### 
		apDisplay.printColor("PART 7: MAKE 1D PLOT SUMMARY FIGURE", "magenta")

		titlefontsize=8
		axisfontsize=7
		raddatasq = raddata**2
		## auto set max location
		showres = (self.res80*self.res50*self.outerAngstrom1D)**(1/3.)
		showres = (showres*self.res50*self.outerAngstrom1D)**(1/3.)
		maxloc = 1.0/showres
		maxlocsq = maxloc**2
		
		pyplot.clf()

		if self.debug is True:
			apDisplay.printColor("1d plot part 1", "blue")
		if 'subplot2grid' in dir(pyplot):
			pyplot.subplot2grid((3,2), (0,0))
		else:
			pyplot.subplot(2,2,1) # 2 rows, 2 columns, plot 1
		pyplot.title("Background Noise Subtraction", fontsize=titlefontsize)
		pyplot.ylabel("Log(PSD)", fontsize=axisfontsize)
		pyplot.plot(raddata[fpi:], rotdata[fpi:], 
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddata[fpi:], rotdata[fpi:], 
			'.', color="blue", alpha=0.75, markersize=2.0)
		pyplot.plot(raddata[fpi:], fitvalleydata[fpi:],
			'-', color="darkgreen", alpha=0.25, linewidth=1.0)
		
		colorList = ['magenta', 'darkred', 'darkorange', 'darkgoldenrod', 'darkgreen', ]
		for section in range(numSections):
			startIndex = noiseStartIndexes[section]
			endIndex = noiseEndIndexes[section]
			color = colorList[section % len(colorList)]
			pyplot.plot(raddata[startIndex:endIndex], noiseDataList[section][startIndex:endIndex],
				'-', color=color, alpha=0.5, linewidth=2)

		pyplot.plot(raddata[fpi:], noisedata[fpi:], 
			'--', color="purple", alpha=1.0, linewidth=1)
		self.setPyPlotXLabels(raddata, valleyradii=valleyradii, maxloc=maxloc, square=False)
		pyplot.ylim(ymin=noisedata.min())

		if self.debug is True:
			apDisplay.printColor("1d plot part 2", "blue")
		if 'subplot2grid' in dir(pyplot):
			pyplot.subplot2grid((3,2), (0,1))
		else:
			pyplot.subplot(2,2,2) # 2 rows, 2 columns, plot 2
		pyplot.title("Envelope Normalization", fontsize=titlefontsize)
		pyplot.ylabel("Log(PSD-Noise)", fontsize=axisfontsize)
		pyplot.plot(raddata[fpi:], normlogrotdata[fpi:],
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddata[fpi:], normlogrotdata[fpi:],
			'.', color="blue", alpha=0.75, markersize=2.0)
		pyplot.plot(raddata[fpi:], numpy.log(fitpeakdata[fpi:]),
			'-', color="darkgreen", alpha=0.25, linewidth=1.0)


		for section in range(numSections):
			startIndex = envelopStartIndexes[section]
			endIndex = envelopEndIndexes[section]
			color = colorList[section % len(colorList)]
			pyplot.plot(raddata[startIndex:endIndex], numpy.log(envelopDataList[section][startIndex:endIndex]),
				'-', color=color, alpha=0.5, linewidth=2)

		logenvelopdata = numpy.log(envelopdata)
		pyplot.plot(raddata[fpi:], logenvelopdata[fpi:],
			'--', color="purple", alpha=1.0, linewidth=1)
		self.setPyPlotXLabels(raddata, peakradii=peakradii, maxloc=maxloc, square=False)
		pyplot.ylim(ymax=logenvelopdata.max())

		if self.debug is True:
			apDisplay.printColor("1d plot part 3", "blue")
		if 'subplot2grid' in dir(pyplot):
			pyplot.subplot2grid((3,2), (1,0), colspan=2)
		else:
			pyplot.subplot(2,2,3) # 2 rows, 2 columns, plot 3
		pyplot.title("Fit of CTF data (30-10A %.3f / 5-peak %.3f) Def1= %.3e / Def2= %.3e"
			%(self.conf3010, self.conf5peak, self.defocus1, self.defocus2), fontsize=titlefontsize)
		pyplot.ylabel("Norm PSD", fontsize=titlefontsize)
		pyplot.plot(raddatasq[fpi:], ctffitdata[fpi:],
			'-', color="black", alpha=0.5, linewidth=1)
		#pyplot.plot(raddatasq[fpi:], overctffitdata[fpi:],
		#	'-', color="red", alpha=0.75, linewidth=1)
		pyplot.plot(raddatasq[fpi:], normpeakdata[fpi:],
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddatasq[fpi:], normpeakdata[fpi:],
			'.', color="blue", alpha=0.75, markersize=2.0)
		self.setPyPlotXLabels(raddatasq, maxloc=maxlocsq, square=True)
		pyplot.grid(True, linestyle=':', )
		pyplot.ylim(-0.05, 1.05)

		"""
		pyplot.subplot2grid((3,2), (1,1))
		tenangindex = numpy.searchsorted(raddata, 1/10.)-1
		pyplot.title("Defocus1= %.3e / Defocus2= %.3e"
			%(self.defocus1, self.defocus2), fontsize=titlefontsize)
		pyplot.ylabel("Norm PSD", fontsize=titlefontsize)
		pyplot.plot(raddatasq[tenangindex:], ctffitdata[tenangindex:],
			'-', color="black", alpha=0.5, linewidth=1)
		pyplot.plot(raddatasq[tenangindex:], normpeakdata[tenangindex:],
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddatasq[tenangindex:], normpeakdata[tenangindex:],
			'.', color="blue", alpha=0.75, markersize=2.0)
		self.setPyPlotXLabels(raddatasq[tenangindex:], maxloc=1/7.**2, square=True)
		pyplot.grid(True, linestyle=':', )
		pyplot.ylim(-0.05, 1.05)
		"""

		confraddatasq = confraddata**2
		if self.debug is True:
			apDisplay.printColor("1d plot part 4", "blue")
		if 'subplot2grid' in dir(pyplot):
			pyplot.subplot2grid((3,2), (2,0), colspan=2)
			pyplot.title(r'Resolution limits: %.2f$\AA$ at 0.8 and %.2f$\AA$ at 0.5'
				%(self.res80, self.res50), fontsize=titlefontsize)
		else:
			pyplot.subplot(2,2,4) # 2 rows, 2 columns, plot 4
			pyplot.title('Resolution limits: %.2fA at 0.8 and %.2fA at 0.5'
				%(self.res80, self.res50), fontsize=titlefontsize)
		pyplot.ylabel("Correlation", fontsize=titlefontsize)
		pyplot.plot(raddatasq[fpi:], ctffitdata[fpi:],
			'-', color="black", alpha=0.2, linewidth=1)
		pyplot.plot(raddatasq[fpi:], normpeakdata[fpi:],
			'-', color="blue", alpha=0.2, linewidth=1)
		#pyplot.plot(raddatasq[fpi:], normpeakdata[fpi:],
		#	'.', color="black", alpha=0.25, markersize=1.0)
		pyplot.axvline(x=1.0/self.res80**2, linewidth=2, color="gold", alpha=0.75, ymin=0, ymax=0.8)
		pyplot.axvline(x=1.0/self.res50**2, linewidth=2, color="red", alpha=0.75, ymin=0, ymax=0.5)
		res80index = numpy.searchsorted(confraddata, 1.0/self.res80)
		pyplot.plot(confraddatasq[:res80index+1], confdata[:res80index+1],
			'-', color="green", alpha=1, linewidth=2)
		res50index = numpy.searchsorted(confraddata, 1.0/self.res50)
		pyplot.plot(confraddatasq[res80index-1:res50index+1], confdata[res80index-1:res50index+1],
			'-', color="orange", alpha=1, linewidth=2)
		pyplot.plot(confraddatasq[res50index-1:], confdata[res50index-1:],
			'-', color="red", alpha=1, linewidth=2)
		self.setPyPlotXLabels(raddatasq, maxloc=maxlocsq, square=True)
		pyplot.grid(True, linestyle=':', )
		if self.res80 < 99:
			pyplot.ylim(-0.05, 1.05)
		elif self.res50 < 99:
			pyplot.ylim(-0.25, 1.05)
		else:
			pyplot.ylim(-0.55, 1.05)

		pyplot.subplots_adjust(wspace=0.22, hspace=0.50, 
			bottom=0.08, left=0.07, top=0.95, right=0.965, )
		self.plotsfile = apDisplay.short(self.imgname)+"-plots.png"
		apDisplay.printMsg("Saving 1D graph to file %s"%(self.plotsfile))
		pyplot.savefig(self.plotsfile, format="png", dpi=300, orientation='landscape', pad_inches=0.0)

		if self.debug is True:
			print "Showing results"
			#pyplot.show()
			#plotspng = Image.open(self.plotsfile)
			#plotspng.show()
		pyplot.clf()

		### FIXME
		#if twod is False:
		return zdata2d

		### 
		### PART 8: NORMALIZE THE 2D IMAGE
		### 
		apDisplay.printColor("PART 8: NORMALIZE THE 2D IMAGE", "magenta")

		"""
		print zdata2d.shape
		print pixelrdata.shape
		print noisedata.shape
		print envelopdata.shape
		print valleydata.shape
		print peakdata.shape
		"""

		### Convert 1D array into 2D array by un-elliptical average
		noise2d = ctftools.unEllipticalAverage(pixelrdata, noisedata,
			self.ellipratio, self.angle, zdata2d.shape)
		envelop2d = ctftools.unEllipticalAverage(pixelrdata, envelopdata,
			self.ellipratio, self.angle, zdata2d.shape)
		valley2d = ctftools.unEllipticalAverage(pixelrdata, valleydata,
			self.ellipratio, self.angle, zdata2d.shape)
		peak2d = ctftools.unEllipticalAverage(pixelrdata, peakdata,
			self.ellipratio, self.angle, zdata2d.shape)

		### Do the normalization on the 2d data
		#blur2d = ndimage.gaussian_filter(zdata2d, 2)
		normal2d = numpy.exp(zdata2d) - numpy.exp(noise2d)
		normal2d = normal2d / numpy.exp(envelop2d)
		normal2d = normal2d - valley2d
		normal2d = normal2d / peak2d
		normal2d = numpy.where(normal2d < -0.2, -0.2, normal2d)
		normal2d = numpy.where(normal2d > 1.2, 1.2, normal2d)
		return normal2d

	#====================
	#====================
	def trimDataToExtrema(self, xdata, rawdata, extrema):
		trimxdata = []
		trimrawdata = []
		for i in range(len(extrema)):
			exvalue = extrema[i]
			index = numpy.searchsorted(xdata, exvalue)
			trimxdata.extend(xdata[index-10:index+10])
			trimrawdata.extend(rawdata[index-10:index+10])
		return numpy.array(trimxdata), numpy.array(trimrawdata)

	#====================
	#====================
	def setPyPlotXLabels(self, xdata, peakradii=None, valleyradii=None, square=False, maxloc=None):
		"""
		assumes xdata is in units of 1/Angstroms
		"""
		minloc = xdata.min()
		if maxloc is None:
			maxloc = xdata.max()
		xstd = xdata.std()/2.
		pyplot.xlim(xmin=minloc, xmax=maxloc)
		locs, labels = pyplot.xticks()
		if square is True:
			if 'subplot2grid' in dir(pyplot):
				units = r'$\AA^2$'
			else:
				units = r'$\mathregular{A^2}$'
		else:
			if 'subplot2grid' in dir(pyplot):
				units = r'$\AA$'
			else:
				units = 'A'

		### assumes that x values are 1/Angstroms^2, which give the best plot
		newlocs = []
		newlabels = []
		if self.debug is True:
			print "maxloc=", maxloc
		for loc in locs:
			if loc < minloc + xstd/4:
				continue
			if square is True:
				origres = 1.0/math.sqrt(loc)
			else:
				origres = 1.0/loc
			if origres > 50:
				trueres = round(origres/10.0)*10
			if origres > 25:
				trueres = round(origres/5.0)*5
			elif origres > 12:
				trueres = round(origres/2.0)*2
			elif origres > 7.5:
				trueres = round(origres)
			else:
				trueres = round(origres*2)/2.0

			if square is True:
				trueloc = 1.0/trueres**2
			else:
				trueloc = 1.0/trueres
			#print ("Loc=%.4f, Res=%.2f, TrueRes=%.1f, TrueLoc=%.4f"	
			#	%(loc, origres, trueres, trueloc))
			if trueloc > maxloc - xstd:
				continue
			if trueres < 10 and (trueres*2)%2 == 1:
				label = r'1/%.1f%s'%(trueres, units)
			else:
				label = r'1/%d%s'%(trueres, units)
			if not label in newlabels:
				newlabels.append(label)
				newlocs.append(trueloc)
		#add final value
		newlocs.append(minloc)
		if square is True:
			minres = 1.0/math.sqrt(minloc)
		else:
			minres = 1.0/minloc
		label = "1/%d%s"%(minres, units)
		newlabels.append(label)

		newlocs.append(maxloc)
		if square is True:
			maxres = 1.0/math.sqrt(maxloc)
		else:
			maxres = 1.0/maxloc			
		label = "1/%.1f%s"%(maxres, units)
		newlabels.append(label)

		# set the labels
		pyplot.yticks(fontsize=8)
		pyplot.xticks(newlocs, newlabels, fontsize=7)

		if square is True:
			pyplot.xlabel(r"Resolution ($\mathregular{s^2}$)", fontsize=9)
		else:
			pyplot.xlabel("Resolution (s)", fontsize=9)
		if peakradii is not None:
			for i, rad in enumerate(peakradii):
				if rad < minloc:
					continue
				elif rad > maxloc:
					break
				else:
					pyplot.axvline(x=rad, linewidth=0.5, color="cyan", alpha=0.5)
		if valleyradii is not None:
			for i, rad in enumerate(valleyradii):
				if rad < minloc:
					continue
				elif rad > maxloc:
					break
				else:
					pyplot.axvline(x=rad, linewidth=0.5, color="gold", alpha=0.5)

		return

	#====================
	#====================
	def drawPowerSpecImage(self, origpowerspec, maxsize=1200):
		origpowerspec = ctftools.trimPowerSpectraToOuterResolution(origpowerspec, self.plotlimit2DAngstrom, self.trimfreq)

		if self.debug is True:
			print "origpowerspec shape", origpowerspec.shape

		#compute elliptical average and merge with original image
		pixelrdata, rotdata = ctftools.ellipticalAverage(origpowerspec, self.ellipratio, self.angle,
			self.ringwidth*3, 1, full=True)
		ellipavgpowerspec = ctftools.unEllipticalAverage(pixelrdata, rotdata, 
			self.ellipratio, self.angle, origpowerspec.shape)
		halfshape = origpowerspec.shape[1]/2
		halfpowerspec = numpy.hstack( (origpowerspec[:,:halfshape] , ellipavgpowerspec[:,halfshape:] ) )
		if halfpowerspec.shape != origpowerspec.shape:
			apDisplay.printError("Error in power spectra creation")

		if max(halfpowerspec.shape) > maxsize:
			scale = maxsize/float(max(halfpowerspec.shape))
			#scale = math.sqrt((random.random()+random.random()+random.random())/3.0)
			apDisplay.printMsg( "Scaling final powerspec image by %.3f"%(scale))
			powerspec = imagefilter.scaleImage(halfpowerspec, scale)
		else:
			scale = 1280./float(max(halfpowerspec.shape))
			powerspec = imagefilter.scaleImage(halfpowerspec, scale)
			#scale = 1.0
			#powerspec = halfpowerspec.copy()

		self.scaleapix = self.trimapix
		self.scalefreq = self.trimfreq/scale
		if self.debug is True:
			print "orig pixel", self.apix
			print "trim pixel", self.trimapix
			print "scale pixel", self.scaleapix

		numzeros = 13

		radii1 = ctftools.getCtfExtrema(self.defocus1, self.scalefreq*1e10, 
			self.cs, self.volts, self.ampcontrast, numzeros=numzeros, zerotype="valley")
		radii2 = ctftools.getCtfExtrema(self.defocus2, self.scalefreq*1e10, 
			self.cs, self.volts, self.ampcontrast, numzeros=numzeros, zerotype="valley")

		#smallest of two defocii
		firstpeak = radii2[0]

		### 
		### PART 9: DRAW THE 2D POWERSPEC IMAGE
		### 
		center = numpy.array(powerspec.shape, dtype=numpy.float)/2.0
		foundzeros = min(len(radii1), len(radii2))
		"""
		pyplot.clf()
		ax = pyplot.subplot(1,1,1)
		pyplot.xticks([], [])
		pyplot.yticks([], [])
		pyplot.imshow(powerspec)
		pyplot.gray()
		for i in range(foundzeros):
			# because |def1| < |def2| ==> firstzero1 > firstzero2
			major = radii1[i]*2
			minor = radii2[i]*2
			ell = Ellipse(xy=center, width=major, height=minor, angle=self.angle+90, 
				fill=False, edgecolor="yellow", antialiased=True, linewidth=0.5)
			ax.add_artist(ell)
		pyplot.subplots_adjust(wspace=0, hspace=0, bottom=0, left=0, top=1, right=1, )
		self.newpowerspecfile = apDisplay.short(self.imgname)+"-powerspec-new.png"
		pyplot.savefig(self.newpowerspecfile, format="png", dpi=150, pad_inches=0.0)
		"""

		### 
		### PART 9: DRAW THE 2D POWERSPEC IMAGE
		### 
		apDisplay.printColor("PART 9: DRAW THE 2D POWERSPEC IMAGE", "magenta")

		center = numpy.array(powerspec.shape, dtype=numpy.float)/2.0
		originalimage = imagefile.arrayToImage(powerspec)
		originalimage = originalimage.convert("RGB")
		pilimage = originalimage.copy()
		draw = ImageDraw.Draw(pilimage)

		#########
		## draw astig axis line, if astig > 5%
		#########
		perdiff = 2*abs(self.defocus1-self.defocus2)/abs(self.defocus1+self.defocus2)
		if self.debug is True:
			print "Percent Difference %.1f"%(perdiff*100)
		if perdiff > 0.05:
			#print self.angle, radii2[0], center
			x = 1*firstpeak*math.cos(math.radians(self.angle))
			y = firstpeak*math.sin(math.radians(self.angle))
			#print x,y
			xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
			#print xy
			draw.line(xy, fill="#f23d3d", width=10)
		elif perdiff > 1e-6:
			#print self.angle, radii2[0], center
			x = 1*firstpeak*math.cos(math.radians(self.angle))
			y = firstpeak*math.sin(math.radians(self.angle))
			#print x,y
			xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
			#print xy
			draw.line(xy, fill="#f23d3d", width=2)

		#########
		## draw colored CTF Thon rings
		#########
		foundzeros = min(len(radii1), len(radii2))
		for i in range(foundzeros):

			# because |def1| < |def2| ==> firstzero1 > firstzero2
			major = radii1[i]
			minor = radii2[i]
			if self.debug is True: 
				print "major=%.1f, minor=%.1f, angle=%.1f"%(major, minor, self.angle)
			if minor > powerspec.shape[0]/math.sqrt(3):
				# this limits how far we draw out the ellipses sqrt(3) to corner, just 2 inside line
				break
			width = int(math.ceil(math.sqrt(numzeros - i)))*2

			### determine color of circle
			currentres = 1.0/(major*self.scalefreq)
			if currentres > self.res80:
				ringcolor = "green"
			elif currentres > self.res50:
				ringcolor = "gold"
			else:
				ringcolor = "red"

			### determine number of points to use to draw ellipse, minimize distance btw points
			#isoceles triangle, b: radius ot CTF ring, a: distance btw points
			#a = 2 * b sin (theta/2)
			#a / 2b = sin(theta/2)
			#theta = 2 * asin (a/2b)
			#numpoints = 2 pi / theta
			## define a to be 5 pixels
			a = 40
			theta = 2.0 * math.asin (a/(2.0*major))
			skipfactor = 2
			numpoints = int(math.ceil(2.0*math.pi/theta/skipfactor))*skipfactor + 1
			#print "numpoints", numpoints


			points = ellipse.generate_ellipse(major, minor, 
				math.radians(self.angle), center, numpoints, None, "step", True)
			x = points[:,0]
			y = points[:,1]

			## wrap around to end
			x = numpy.hstack((x, [x[0],]))
			y = numpy.hstack((y, [y[0],]))
			## convert image

			numsteps = int(math.floor((len(x)-2)/skipfactor))
			for j in range(numsteps):
				k = j*skipfactor
				xy = (x[k], y[k], x[k+1], y[k+1])
				draw.line(xy, fill=ringcolor, width=width)

		#########
		## draw blue resolution ring
		#########
		# 1/res = freq * pixrad => pixrad = 1/(res*freq)
		maxrad = (max(powerspec.shape)-1)/2.0 - 3
		maxres = 1.0/(self.scalefreq*maxrad)
		bestres = math.ceil(maxres)
		pixrad = 1.0/(self.scalefreq*bestres)
		if self.debug is True:
			print "bestres %d Angstroms (max: %.3f)"%(bestres, maxres)
			print "pixrad %d (max: %.3f)"%(pixrad, maxrad)
		if pixrad > maxrad:
			apDisplay.printError("Too big of outer radius to draw")
		for i in numpy.arange(-4.0,4.01,0.01):
			r = pixrad + i
			blackxy = numpy.array((center[0]-r,center[1]-r, 
				center[0]+r,center[1]+r), dtype=numpy.float64)
			draw.ellipse(tuple(blackxy), outline="black")
		for i in numpy.arange(-1.50,1.51,0.01):
			r = pixrad + i
			whitexy = numpy.array((center[0]-r,center[1]-r, 
				center[0]+r,center[1]+r), dtype=numpy.float64)
			draw.ellipse(tuple(whitexy), outline="#0BB5FF")

		#########
		## setup font to add text
		#########
		fontpath = "/usr/share/fonts/liberation/LiberationSans-Regular.ttf"
		from PIL import ImageFont
		if os.path.isfile(fontpath):
			fontsize = int(math.ceil( 48/2. * min(powerspec.shape)/float(maxsize))*2)
			font = ImageFont.truetype(fontpath, fontsize)
		else:
			font = ImageFont.load_default()

		#########
		## add resolution ring text
		#########
		angrad = maxrad/math.sqrt(2) + 1
		coord = (angrad+maxrad, angrad+maxrad)
		for i in [-2,2]:
			for j in [-2,2]:
				draw.text((coord[0]+i,coord[1]+j), "%.1f A"%(bestres), font=font, fill="black")
		draw.text(coord, "%.1f A"%(bestres), font=font, fill="#0BB5FF")

		#########
		## add defocus value text
		#########
		meandef = abs(self.defocus1+self.defocus2)/2.0
		deftext = "%.2f um"%(meandef*1e6)
		tsize = draw.textsize(deftext, font=font)
		coord = (powerspec.shape[0]-4-tsize[0], powerspec.shape[0]-4-tsize[1])
		for i in [-2,2]:
			for j in [-2,2]:
				draw.text((coord[0]+i,coord[1]+j), deftext, font=font, fill="black")
		draw.text(coord, deftext, font=font, fill="#AB82FF")

		#########
		## add text about what sides of powerspec are:
		## left - raw data; right - elliptical average data
		#########
		leftcoord = (4, 4)
		for i in [-3, -1, 0, 1, 3]:
			for j in [-3, -1, 0, 1, 3]:
				draw.text((leftcoord[0]+i,leftcoord[1]+j) , "Raw CTF Data", font=font, fill="black")
		draw.text(leftcoord, "Raw CTF Data", font=font, fill="#00BFFF")

		tsize = draw.textsize("Elliptical Average", font=font)
		xdist = powerspec.shape[0] - 4 - tsize[0]
		rightcoord = (xdist, 4)
		for i in [-2,2]:
			for j in [-2,2]:
				draw.text((rightcoord[0]+i,rightcoord[1]+j), "Elliptical Average", font=font, fill="black")
		draw.text(rightcoord, "Elliptical Average", font=font, fill="#00BFFF")

		#########
		## create an alpha blend effect
		#########
		originalimage = Image.blend(originalimage, pilimage, 0.95)
		apDisplay.printMsg("Saving 2D powerspectra to file: %s"%(self.powerspecfile))
		#pilimage.save(self.powerspecfile, "JPEG", quality=85)
		originalimage.save(self.powerspecfile, "JPEG", quality=85)
		if not os.path.isfile(self.powerspecfile):
			apDisplay.printWarning("power spec file not created")
		if self.debug is True:
			#powerspecjpg = Image.open(self.powerspecfile)
			#powerspecjpg.show()
			pass
		return

	#====================
	#====================
	def convertDefociToConvention(self, ctfdata):
		ctfdb.printCtfData(ctfdata)

		# program specific corrections?
		self.angle = ctfdata['angle_astigmatism']
		#angle = round(self.angle/2.5,0)*2.5

		#by convention: abs(ctfdata['defocus1']) < abs(ctfdata['defocus2'])
		if abs(ctfdata['defocus1']) > abs(ctfdata['defocus2']):
			# incorrect, need to shift angle by 90 degrees
			apDisplay.printWarning("|def1| > |def2|, flipping defocus axes")
			self.defocus1 = ctfdata['defocus2']
			self.defocus2 = ctfdata['defocus1']
			self.angle += 90
		else:
			# correct, ratio > 1
			self.defocus1 = ctfdata['defocus1']
			self.defocus2 = ctfdata['defocus2']
		if self.defocus1 < 0 and self.defocus2 < 0:
			apDisplay.printWarning("Negative defocus values, taking absolute value")
			self.defocus1 = abs(self.defocus1)
			self.defocus2 = abs(self.defocus2)
		self.defdiff = self.defocus1 - self.defocus2
		#elliptical ratio is ratio of zero locations NOT defocii
		self.defocusratio = self.defocus2/self.defocus1
		self.ellipratio = ctftools.defocusRatioToEllipseRatio(self.defocus1, self.defocus2, 
			self.initfreq, self.cs, self.volts, self.ampcontrast)

		# get angle within range -90 < angle <= 90
		while self.angle > 90:
			self.angle -= 180
		while self.angle < -90:
			self.angle += 180

		apDisplay.printColor("Final params: def1: %.2e | def2: %.2e | angle: %.1f | defratio %.2f"%
			(self.defocus1, self.defocus2, self.angle, self.defocusratio), "cyan")

		perdiff = abs(self.defocus1-self.defocus2)/abs(self.defocus1+self.defocus2)
		apDisplay.printMsg("Defocus Astig Percent Diff %.2f -- %.3e, %.3e"
				%(perdiff*100,self.defocus1,self.defocus2))

		return

	#====================
	#====================
	def CTFpowerspec(self, imgdata, ctfdata, fftpath=None, fftfreq=None, twod=True):
		"""
		Make a nice looking powerspectra with lines for location of Thon rings

		inputs:
			imgdata - sinedon AcquistionImage table row
			ctfdata - sinedon apCtfData table row
				amplitude constrast - ( a cos + sqrt(1-a^2) sin format)
				defocus1 > defocus2
				angle - in degrees, positive x-axis is zero
			outerbound is now set by self.outerAngstrom1D (in Angstroms)
				outside this radius is trimmed away
		"""
		### setup initial parameters for image
		self.imgname = imgdata['filename']
		if self.debug is True:
			print apDisplay.short(self.imgname)
		self.powerspecfile = apDisplay.short(self.imgname)+"-powerspec.jpg"

		### get peak of CTF
		self.cs = ctfdata['cs']*1e-3
		self.volts = imgdata['scope']['high tension']
		self.ampcontrast = ctfdata['amplitude_contrast']

		### process power spectra
		self.apix = apDatabase.getPixelSize(imgdata)

		if self.debug is True:
			print "Pixelsize (A/pix)", self.apix

		apDisplay.printMsg("Reading image...")
		image = imgdata['image']
		self.initfreq = 1./(self.apix * image.shape[0])
		self.origimageshape = image.shape

		### get correct data
		self.convertDefociToConvention(ctfdata)

		if self.debug is True:
			for key in ctfdata.keys():
				if ctfdata[key] is not None and not isinstance(ctfdata[key], dict):
					print "  ", key, "--", ctfdata[key]

		if fftpath is not None and fftfreq is not None and os.path.isfile(fftpath):
			powerspec = mrc.read(fftpath).astype(numpy.float64)
			self.trimfreq = fftfreq
		else:
			powerspec, self.trimfreq = ctftools.powerSpectraToOuterResolution(image, 
				self.outerAngstrom1D, self.apix)
		self.trimapix = 1.0/(self.trimfreq * powerspec.shape[0])

		#print "Median filter image..."
		#powerspec = ndimage.median_filter(powerspec, 2)
		apDisplay.printMsg("Preform a rotational average and remove spikes...")
		rotfftarray = ctftools.rotationalAverage2D(powerspec)
		stdev = rotfftarray.std()
		rotplus = rotfftarray + stdev*4
		powerspec = numpy.where(powerspec > rotplus, rotfftarray, powerspec)
		#print "Light Gaussian blur image..."
		#powerspec = ndimage.gaussian_filter(powerspec, 3)

		if self.debug is True:
			print "\torig pixel %.3f freq %.3e"%(self.apix, self.initfreq)
			print "\ttrim pixel %.3f freq %.3e"%(self.trimapix, self.trimfreq)

		### more processing
		normpowerspec = self.normalizeCtf(powerspec, twod=twod)
		if normpowerspec is None:
			return None

		if twod is True:
			self.drawPowerSpecImage(normpowerspec)

		ctfdisplaydict = {
			'powerspecfile': self.powerspecfile,
			'plotsfile': self.plotsfile,
			'conf3010': self.conf3010,
			'conf5peak': self.conf5peak,
			'overconf3010': self.overconf3010,
			'overconf5peak': self.overconf5peak,
			'res80': self.res80,
			'res50': self.res50,
			'overres80': self.overres80,
			'overres50': self.overres50,
		}

		return ctfdisplaydict

#====================
#====================
#====================
#====================
if __name__ == "__main__":
	import glob
	import sinedon
	from appionlib import apProject

	imagelist = []
	#=====================
	### CNV data
	#imagelist.extend(glob.glob("/data01/leginon/10apr19a/rawdata/10apr19a_10apr19a_*en_1.mrc"))
	imagelist.extend(glob.glob("/data01/leginon/10apr19a/rawdata/10apr19a_10apr19a_*23gr*10sq*02hl*17en_1.mrc"))
	### Pick-wei images with lots of rings
	#imagelist.extend(glob.glob("/data01/leginon/09sep20a/rawdata/09*en.mrc"))
	### Something else, ice data
	#imagelist.extend(glob.glob("/data01/leginon/09feb20d/rawdata/09*en.mrc"))
	### OK groEL ice data
	#imagelist.extend(glob.glob("/data01/leginon/05may19a/rawdata/05*en*.mrc"))
	### 30S ribosome in stain
	#imagelist.extend(glob.glob("/data01/leginon/12jun06h52a/rawdata/12*en*.mrc"))
	imagelist.extend(glob.glob("/data01/leginon/12jun06h52a/rawdata/12jun06h52a_09oct22c*04sq*19hl*2en*.mrc"))
	### images of Hassan with 1.45/1.65 astig at various angles
	#imagelist.extend(glob.glob("/data01/leginon/12jun12a/rawdata/12jun12a_ctf_image_ang*.mrc"))
	### rectangular images
	#imagelist.extend(glob.glob("/data01/leginon/12may08eD1/rawdata/*.mrc"))
	#=====================

	apDisplay.printMsg("# of images: %d"%(len(imagelist)))
	#imagelist.sort()
	#imagelist.reverse()
	random.shuffle(imagelist)
	#imagelist = imagelist[:30]
	random.shuffle(imagelist)

	
	for imgfile in imagelist:
		apDisplay.printMsg(apDisplay.short(os.path.basename(imgfile)))

	count = 0
	for imgfile in imagelist:
		count += 1
		imagename = os.path.basename(imgfile)
		imagename = imagename.replace(".mrc", "")
		imgdata = apDatabase.getImageData(imagename)

		### change project
		projid = apProject.getProjectIdFromImageData(imgdata)
		newdbname = apProject.getAppionDBFromProjectId(projid)
		sinedon.setConfig('appiondata', db=newdbname)

		powerspecfile = apDisplay.short(imagename)+"-powerspec.jpg"
		if os.path.isfile(powerspecfile):
			apDisplay.printColor("Skipping image %s, already complete"%(apDisplay.short(imagename)), "cyan")
			continue

		ctfdata = ctfdb.getBestCtfByResolution(imgdata)
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ctffind")
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ace2")
		if ctfdata is None:
			apDisplay.printColor("Skipping image %s, no CTF data"%(apDisplay.short(imagename)), "red")
			continue
		#print ctfdata
		if ctfdata['confidence_30_10'] < 0.88:
			apDisplay.printColor("Skipping image %s, poor confidence"%(apDisplay.short(imagename)), "red")
			continue
		"""
		if ctfdata['resolution_50_percent'] > 10 or ctfdata['resolution_50_percent'] < 7.5:
			apDisplay.printColor("Skipping image %s, not right 50per resolution"%(apDisplay.short(imagename)), "red")
			continue
		if ctfdata['resolution_80_percent'] > 13 or ctfdata['resolution_80_percent'] < 8.5:
			apDisplay.printColor("Skipping image %s, not right 80per resolution"%(apDisplay.short(imagename)), "red")
			continue
		if ctfdata['defocus1'] > 2.0e-6:
			apDisplay.printColor("Skipping image %s, too high defocus"%(apDisplay.short(imagename)), "red")
			continue
		"""

		print ""
		print "**********************************"
		print "IMAGE: %s (%d of %d)"%(apDisplay.short(imagename), count, len(imagelist))
		print "**********************************"

		a = CtfDisplay()
		ctfdisplaydict = a.CTFpowerspec(imgdata, ctfdata)
		print "**********************************"

		#if count > 8:
		#	sys.exit(1)

#====================
#====================
#====================
def makeCtfImages(imgdata, ctfdata, fftpath=None, fftfreq=None, twod=True):
	a = CtfDisplay()
	ctfdisplaydict = a.CTFpowerspec(imgdata, ctfdata, fftpath, fftfreq, twod=twod)
	return ctfdisplaydict



