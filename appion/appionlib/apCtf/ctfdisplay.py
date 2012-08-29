#!/usr/bin/env python

import os
import sys
import math
import numpy
import time
import random
from pyami import imagefun
from pyami import ellipse

from appionlib import apDatabase
from appionlib import apDisplay
#from appionlib import lowess
from appionlib.apImage import imagefile
from appionlib.apImage import imagefilter
from matplotlib import use
use('Agg')
from matplotlib import pyplot
from matplotlib.patches import Ellipse
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
		return

	#====================
	#====================
	def funcrad(self, r, rdata=None, zdata=None):
		return numpy.interp(r, rdata, zdata)

	#====================
	#====================
	def Array1dintoArray2d(self, array1d, shape):
		array2d = imagefun.fromRadialFunction(self.funcrad, shape, rdata=rdata, zdata=array1d)
		return array2d

	#====================
	#====================
	def normalizeCtf(self, zdata2d):
		"""
		inner cut radius - radius for number of pixels to clip in the center of image
		"""
		### 
		### PART 1: SETUP PARAMETERS AND ELLIPTICAL AVERAGE
		###
		apDisplay.printColor("PART 1: SETUP PARAMETERS AND ELLIPTICAL AVERAGE", "magenta")

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
		firstvalley = valley[0]
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
		### PART 2: BACKGROUND NOISE SUBTRACTION
		### 
		apDisplay.printColor("PART 2: BACKGROUND NOISE SUBTRACTION", "magenta")

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		firstvalleyindex = numpy.searchsorted(raddata, self.trimfreq*firstvalley)
		numpoints = len(raddata) - firstvalleyindex
		# require at least 10 points past first peak of CTF to perform estimation
		if numpoints < 10:
			return None
		part1start = firstvalleyindex
		part1end = int(firstvalleyindex + numpoints*6/10.)
		part2start = int(firstvalleyindex + numpoints*5/10.)
		part2end = int(firstvalleyindex + numpoints*9/10.)
		part3start = int(firstvalleyindex + numpoints*8/10.)
		part3end = len(raddata)
		
		valleydata = ctfnoise.peakExtender(raddata, rotdata, valleyradii, "below")

		### fit function below log(CTF), i.e., noise model	
		## first part data
		noisefitparams1 = CtfNoise.modelCTFNoise(raddata[part1start:part1end],
			valleydata[part1start:part1end], "below")
		noisedata1 = CtfNoise.noiseModel(noisefitparams1, raddata)

		## second part data
		noisefitparams2 = CtfNoise.modelCTFNoise(raddata[part2start:part2end],
			valleydata[part2start:part2end], "below")
		noisedata2 = CtfNoise.noiseModel(noisefitparams2, raddata)

		## third part data
		noisefitparams3 = CtfNoise.modelCTFNoise(raddata[part3start:part3end],
			valleydata[part3start:part3end], "below")
		noisedata3 = CtfNoise.noiseModel(noisefitparams3, raddata)

		## merge data
		scale = numpy.arange(part1end-part2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = noisedata1[part2start:part1end]*(1-scale) + noisedata2[part2start:part1end]*scale
		scale = numpy.arange(part2end-part3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = noisedata2[part3start:part2end]*(1-scale) + noisedata3[part3start:part2end]*scale

		mergedata = numpy.hstack((noisedata1[:part2start], overlapdata1,
			noisedata2[part1end:part3start], overlapdata2,
			noisedata3[part2end:]))

		noisedata = mergedata

		### DO THE SUBTRACTION
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

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		firstpeakindex = numpy.searchsorted(raddata, firstpeak*self.trimfreq)
		numpoints = len(raddata) - firstpeakindex
		part1start = firstpeakindex
		part1end = int(firstpeakindex + numpoints*6/10.)
		part2start = int(firstpeakindex + numpoints*5/10.)
		part2end = int(firstpeakindex + numpoints*9/10.)
		part3start = int(firstpeakindex + numpoints*8/10.)
		part3end = len(raddata)

		peakdata = ctfnoise.peakExtender(raddata, normlogrotdata, peakradii, "above")

		## first part data
		envelopfitparams1 = CtfNoise.modelCTFNoise(raddata[part1start:part1end],
			peakdata[part1start:part1end], "above")
		envelopdata1 = CtfNoise.noiseModel(envelopfitparams1, raddata)

		## second part data
		envelopfitparams2 = CtfNoise.modelCTFNoise(raddata[part2start:part2end],
			peakdata[part2start:part2end], "above")
		envelopdata2 = CtfNoise.noiseModel(envelopfitparams2, raddata)

		## third part data
		envelopfitparams3 = CtfNoise.modelCTFNoise(raddata[part3start:part3end],
			peakdata[part3start:part3end], "above")
		envelopdata3 = CtfNoise.noiseModel(envelopfitparams3, raddata)

		## merge data
		scale = numpy.arange(part1end-part2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = envelopdata1[part2start:part1end]*(1-scale) + envelopdata2[part2start:part1end]*scale
		scale = numpy.arange(part2end-part3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = envelopdata2[part3start:part2end]*(1-scale) + envelopdata3[part3start:part2end]*scale

		mergedata = numpy.hstack((envelopdata1[:part2start], overlapdata1,
			envelopdata2[part1end:part3start], overlapdata2,
			envelopdata3[part2end:]))
		envelopdata = mergedata

		normnormexprotdata = normexprotdata / numpy.exp(envelopdata)

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
		if self.overconf3010 > self.conf3010:
			apDisplay.printWarning("Image is possibly over-focused")

		ind5peak1 = numpy.searchsorted(raddata, peakradii[0])
		ind5peak2 = numpy.searchsorted(raddata, peakradii[5])
		self.conf5peak = scipy.stats.pearsonr(normpeakdata[ind5peak1:ind5peak2], ctffitdata[ind5peak1:ind5peak2])[0]
		self.overconf5peak = scipy.stats.pearsonr(normpeakdata[ind5peak1:ind5peak2], overctffitdata[ind5peak1:ind5peak2])[0]
		apDisplay.printColor("5 peak confidence is %.3f (overfocus %.3f)"%(self.conf5peak, self.overconf5peak), "green")
		if self.overconf5peak > self.conf5peak:
			apDisplay.printWarning("Image is possibly over-focused")

		### 
		### PART 6: CTF RESOLUTION LIMITS
		### 
		apDisplay.printColor("PART 6: CTF RESOLUTION LIMITS", "magenta")

		confraddata, confdata = ctfres.getCorrelationProfile(raddata, normpeakdata,
			meandefocus, self.trimfreq, self.cs, self.volts, self.ampcontrast)

		self.res80 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.8)
		if self.res80 is None:
			self.res80 = 100.0
		self.res50 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.5)
		if self.res50 is None:
			self.res50 = 100.0
			res50max = min(raddata.max(), 1/10.)
		else:
			res50max = min(raddata.max(), 1.5/self.res50)

		apDisplay.printColor("Resolution limit is %.2f at 0.8 and %.2f at 0.5"
			%(self.res80, self.res50), "green")

		### 
		### PART 7: MAKE 1D PLOT SUMMARY FIGURE
		### 
		apDisplay.printColor("PART 7: MAKE 1D PLOT SUMMARY FIGURE", "magenta")

		titlefontsize=8
		axisfontsize=7
		raddatasq = raddata**2
		confraddatasq = confraddata**2
		valleyradiisq = valleyradii**2
		peakradiisq = peakradii**2
		fpi = firstpeakindex

		pyplot.clf()

		pyplot.subplot(4,2,1) # 3 rows, 2 columns, plot 1
		pyplot.title("Background Noise Subtraction", fontsize=titlefontsize)
		pyplot.ylabel("Log(PSD)", fontsize=axisfontsize)
		pyplot.plot(raddata[fpi:], rotdata[fpi:], 
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddata[fpi:], rotdata[fpi:], 
			'.', color="blue", alpha=0.75, markersize=2.0)
		pyplot.plot(raddata[part1start:part1end], noisedata1[part1start:part1end],
			'-', color="magenta", alpha=0.5, linewidth=2)
		pyplot.plot(raddata[part2start:part2end], noisedata2[part2start:part2end],
			'-', color="red", alpha=0.5, linewidth=2)
		pyplot.plot(raddata[part3start:part3end], noisedata3[part3start:part3end], 
			'-', color="orange", alpha=0.5, linewidth=2)
		pyplot.plot(raddata[fpi:], noisedata[fpi:], 
			'--', color="purple", alpha=1.0, linewidth=1)
		self.setPyPlotXLabels(raddata, valleyradii=valleyradii, maxloc=res50max)
		pyplot.ylim(ymin=noisedata[-1])

		pyplot.subplot(4,2,2) # 3 rows, 2 columns, plot 2
		pyplot.title("Envelope Normalization", fontsize=titlefontsize)
		pyplot.ylabel("Log(PSD-Noise)", fontsize=axisfontsize)
		pyplot.plot(raddata[fpi:], normlogrotdata[fpi:],
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddata[fpi:], normlogrotdata[fpi:],
			'.', color="blue", alpha=0.75, markersize=2.0)
		pyplot.plot(raddata[part1start:part1end], envelopdata1[part1start:part1end],
			'-', color="magenta", alpha=0.5, linewidth=2)
		pyplot.plot(raddata[part2start:part2end], envelopdata2[part2start:part2end],
			'-', color="red", alpha=0.5, linewidth=2)
		pyplot.plot(raddata[part3start:part3end], envelopdata3[part3start:part3end],
			'-', color="orange", alpha=0.5, linewidth=2)
		pyplot.plot(raddata[fpi:], envelopdata[fpi:],
			'--', color="purple", alpha=1.0, linewidth=1)
		self.setPyPlotXLabels(raddata, peakradii=peakradii, maxloc=res50max)
		pyplot.ylim(ymax=envelopdata[fpi-1])

		pyplot.subplot(4,2,3) # 3 rows, 2 columns, plot 3
		pyplot.title("Fit Valley Subtraction", fontsize=titlefontsize)
		pyplot.ylabel("Norm PSD", fontsize=titlefontsize)
		pyplot.plot(raddata[fpi:], normnormexprotdata[fpi:],
			'-', color="blue", alpha=0.5, linewidth=0.75)
		pyplot.plot(raddata[fpi:], normnormexprotdata[fpi:],
			'.', color="blue", alpha=0.75, markersize=1.0)
		pyplot.plot(raddata[fpi:], valleydata[fpi:],
			'-', color="black", alpha=0.75, linewidth=1)
		self.setPyPlotXLabels(raddata, valleyradii=valleyradii, maxloc=res50max)
		pyplot.grid(True, linestyle=':', )
		pyplot.ylim(-0.5, 1.1)

		pyplot.subplot(4,2,4) # 3 rows, 2 columns, plot 4
		pyplot.title("Fit Peak Normalization", fontsize=titlefontsize)
		pyplot.ylabel("Norm PSD", fontsize=titlefontsize)
		pyplot.plot(raddata[fpi:], normvalleydata[fpi:],
			'-', color="blue", alpha=0.5, linewidth=0.75)
		pyplot.plot(raddata[fpi:], normvalleydata[fpi:],
			'.', color="blue", alpha=0.75, markersize=1.0)
		pyplot.plot(raddata[fpi:], peakdata[fpi:],
			'-', color="black", alpha=0.75, linewidth=1)
		self.setPyPlotXLabels(raddata, peakradii=peakradii, maxloc=res50max)
		pyplot.grid(True, linestyle=':', )
		pyplot.ylim(-0.05, 1.5)

		pyplot.subplot(4,2,5) # 3 rows, 2 columns, plot 5
		pyplot.title("Fit of CTF data (30-10A %.3f / 5-peak %.3f)"
			%(self.conf3010, self.conf5peak), fontsize=titlefontsize)
		pyplot.ylabel("Norm PSD", fontsize=titlefontsize)
		pyplot.plot(raddatasq[fpi:], ctffitdata[fpi:],
			'-', color="black", alpha=0.5, linewidth=1)
		pyplot.plot(raddatasq[fpi:], normpeakdata[fpi:],
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddatasq[fpi:], normpeakdata[fpi:],
			'.', color="blue", alpha=0.75, markersize=2.0)
		self.setPyPlotXLabels(raddatasq, maxloc=1/10.**2, square=True)
		pyplot.grid(True, linestyle=':', )
		pyplot.ylim(-0.05, 1.05)

		pyplot.subplot(4,2,6) # 3 rows, 2 columns, plot 6
		pyplot.title("Resolution limits: %.2fA at 0.8 and %.2fA at 0.5"
			%(self.res80, self.res50), fontsize=titlefontsize)
		pyplot.ylabel("Correlation", fontsize=titlefontsize)
		pyplot.plot(raddata[fpi:], ctffitdata[fpi:],
			'-', color="black", alpha=0.2, linewidth=1)
		pyplot.plot(raddata[fpi:], normpeakdata[fpi:],
			'-', color="blue", alpha=0.2, linewidth=1)
		#pyplot.plot(raddata[fpi:], normpeakdata[fpi:],
		#	'.', color="black", alpha=0.25, markersize=1.0)
		pyplot.axvline(x=1.0/self.res80, linewidth=2, color="gold", alpha=0.95, ymin=0, ymax=0.8)
		pyplot.axvline(x=1.0/self.res50, linewidth=2, color="red", alpha=0.95, ymin=0, ymax=0.5)
		res80index = numpy.searchsorted(confraddata, 1.0/self.res80)
		pyplot.plot(confraddata[:res80index+1], confdata[:res80index+1],
			'-', color="green", alpha=1, linewidth=2)
		res50index = numpy.searchsorted(confraddata, 1.0/self.res50)
		pyplot.plot(confraddata[res80index-1:res50index+1], confdata[res80index-1:res50index+1],
			'-', color="orange", alpha=1, linewidth=2)
		pyplot.plot(confraddata[res50index-1:], confdata[res50index-1:],
			'-', color="red", alpha=1, linewidth=2)
		self.setPyPlotXLabels(raddata, maxloc=res50max)
		pyplot.grid(True, linestyle=':', )
		if self.res80 < 99:
			pyplot.ylim(-0.05, 1.05)
		elif self.res50 < 99:
			pyplot.ylim(-0.25, 1.05)
		else:
			pyplot.ylim(-0.55, 1.05)

		pyplot.subplot(4,2,7) # 4 rows, 2 columns, plot 7
		tenangindex = numpy.searchsorted(raddata, 1/10.*self.trimfreq)
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

		pyplot.subplot(4,2,8) # 4 rows, 2 columns, plot 7
		tenangindex = numpy.searchsorted(raddata, 1/10.*self.trimfreq)
		pyplot.title("Overfocus check (30-10A %.3f / 5-peak %.3f)"
			%(self.overconf3010, self.overconf5peak), fontsize=titlefontsize)
		pyplot.ylabel("Norm PSD", fontsize=titlefontsize)
		pyplot.plot(raddatasq[tenangindex:], ctffitdata[tenangindex:],
			'-', color="black", alpha=0.5, linewidth=1)
		pyplot.plot(raddatasq[fpi:], overctffitdata[fpi:],
			'-', color="red", alpha=0.75, linewidth=1)
		pyplot.plot(raddatasq[tenangindex:], normpeakdata[tenangindex:],
			'-', color="blue", alpha=0.5, linewidth=0.5)
		pyplot.plot(raddatasq[tenangindex:], normpeakdata[tenangindex:],
			'.', color="blue", alpha=0.75, markersize=2.0)
		self.setPyPlotXLabels(raddatasq[tenangindex:], maxloc=1/7.**2, square=True)
		pyplot.grid(True, linestyle=':', )
		pyplot.ylim(-0.05, 1.05)

		pyplot.subplots_adjust(wspace=0.22, hspace=0.70, 
			bottom=0.08, left=0.07, top=0.95, right=0.965, )
		self.plotsfile = apDisplay.short(self.imgname)+"-plots.png"
		apDisplay.printMsg("Saving 1D graph to file %s"%(self.plotsfile))
		pyplot.savefig(self.plotsfile, format="png", dpi=200, orientation='landscape', pad_inches=0.0)

		if self.debug is True:
			print "Showing results"
			#pyplot.show()
			#plotspng = Image.open(self.plotsfile)
			#plotspng.show()
		pyplot.clf()

		### 
		### PART 8: NORMALIZE THE 2D IMAGE
		### 
		apDisplay.printColor("PART 8: NORMALIZE THE 2D IMAGE", "magenta")

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

		### assumes that x values are 1/Angstroms^2, which give the best plot
		newlocs = []
		newlabels = []
		#print "maxloc=", maxloc
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
				label = "1/%.1fA"%(trueres)
			else:
				label = "1/%dA"%(trueres)
			if not label in newlabels:
				newlabels.append(label)
				newlocs.append(trueloc)
		#add final value
		newlocs.append(minloc)
		if square is True:
			minres = 1.0/math.sqrt(minloc)
		else:
			minres = 1.0/minloc
		label = "1/%dA"%(minres)
		newlabels.append(label)

		newlocs.append(maxloc)
		if square is True:
			maxres = 1.0/math.sqrt(maxloc)
		else:
			maxres = 1.0/maxloc
		label = "1/%.1fA"%(maxres)
		newlabels.append(label)

		# set the labels
		pyplot.yticks(fontsize=8)
		pyplot.xticks(newlocs, newlabels, fontsize=7)

		if square is True:
			pyplot.xlabel("Resolution (s^2)", fontsize=9)
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
	def drawPowerSpecImage(self, origpowerspec, maxsize=1500, outerresolution=8.7):
		origpowerspec = ctftools.trimPowerSpectraToOuterResolution(origpowerspec, outerresolution, self.trimfreq)

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
			scale = 1.0
			powerspec = halfpowerspec.copy()

		self.scaleapix = self.trimapix
		self.scalefreq = self.trimfreq/scale
		if self.debug is True:
			print "orig pixel", self.apix
			print "trim pixel", self.trimapix
			print "scale pixel", self.scaleapix

		numzeros = 10

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

		## draw an axis line, if astig > 5%
		perdiff = 2*abs(self.defocus1-self.defocus2)/abs(self.defocus1+self.defocus2)
		if self.debug is True:
			print "Percent Difference %.1f"%(perdiff*100)
		if perdiff > 0.05:
			#print self.angle, radii2[0], center
			x = -1*firstpeak*math.cos(math.radians(self.angle))
			y = firstpeak*math.sin(math.radians(self.angle))
			#print x,y
			xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
			#print xy
			draw.line(xy, fill="#f23d3d", width=10)
		elif perdiff > 1e-6:
			#print self.angle, radii2[0], center
			x = -1*firstpeak*math.cos(math.radians(self.angle))
			y = firstpeak*math.sin(math.radians(self.angle))
			#print x,y
			xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
			#print xy
			draw.line(xy, fill="#f23d3d", width=2)

		foundzeros = min(len(radii1), len(radii2))
		#color="#3d3dd2" #blue
		color="#ffd700" #gold
		for i in range(foundzeros):

			# because |def1| < |def2| ==> firstzero1 > firstzero2
			major = radii1[i]
			minor = radii2[i]
			if self.debug is True: 
				print "major=%.1f, minor=%.1f, angle=%.1f"%(major, minor, self.angle)
			if minor > powerspec.shape[0]/math.sqrt(3):
				# this limits how far we draw out the ellipses sqrt(3) to corner, just 2 inside line
				break
			width = int(math.ceil(math.sqrt(numzeros - i)))

			### determine color of circle
			currentres = 1.0/(major*self.trimfreq)
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
			a = 10
			theta = 2.0 * math.asin (a/(2.0*major))
			skipfactor = 3
			numpoints = int(math.ceil(2.0*math.pi/theta/skipfactor))*skipfactor + 1
			#print "numpoints", numpoints


			### for some reason, we need to give a negative angle here
			points = ellipse.generate_ellipse(major, minor, 
				-math.radians(self.angle), center, numpoints, None, "step", True)
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
		outpixrad = math.ceil(pixrad)+1
		inpixrad = math.floor(pixrad)-1
		for i in numpy.arange(-2.0,2.01,0.1):
			r = pixrad + i
			blackxy = numpy.array((center[0]-r,center[1]-r, 
				center[0]+r,center[1]+r), dtype=numpy.float64)
			draw.ellipse(tuple(blackxy), outline="black")
		for i in numpy.arange(-0.5,0.51,0.1):
			r = pixrad + i
			whitexy = numpy.array((center[0]-r,center[1]-r, 
				center[0]+r,center[1]+r), dtype=numpy.float64)
			draw.ellipse(tuple(whitexy), outline="blue")

		### add text
		fontpath = "/usr/share/fonts/liberation/LiberationSans-Regular.ttf"
		from PIL import ImageFont
		if os.path.isfile(fontpath):
			fontsize = int(math.ceil( 48/2. * min(powerspec.shape)/float(maxsize))*2)
			font = ImageFont.truetype(fontpath, fontsize)
		else:
			font = ImageFont.load_default()
		angrad = maxrad/math.sqrt(2) + 10
		coord = (angrad+maxrad, angrad+maxrad)
		draw.text(coord, "%.1f A"%(bestres), font=font, fill="blue")

		## add text about what sides of powerspec are:
		## left - raw data; right - elliptical average data
		leftcoord = (16, 16)
		draw.text(leftcoord, "Raw CTF Data", font=font, fill="blue")
		draw.text(leftcoord, "Raw CTF Data", font=font, fill="black")
		tsize = draw.textsize("Elliptical Average", font=font)
		xdist = powerspec.shape[0] - 16 - tsize[0]
		rightcoord = (xdist, 16)
		draw.text(rightcoord, "Elliptical Average", font=font, fill="blue")

		## create an alpha blend effect
		originalimage = Image.blend(originalimage, pilimage, 0.95)
		apDisplay.printMsg("Saving 2D powerspectra to file: %s"%(self.powerspecfile))
		#pilimage.save(self.powerspecfile, "JPEG", quality=85)
		originalimage.save(self.powerspecfile, "JPEG", quality=85)
		if self.debug is True:
			#powerspecjpg = Image.open(self.powerspecfile)
			#powerspecjpg.show()
			pass
		return

	#====================
	#====================
	def convertDefociToConvention(self, ctfdata):
		ctfdb.printCtfData(ctfdata)
		initdefocusratio = ctfdata['defocus2']/ctfdata['defocus1']

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
	def CTFpowerspec(self, imgdata, ctfdata, outerbound=5e-10):
		"""
		Make a nice looking powerspectra with lines for location of Thon rings

		inputs:
			imgdata - sinedon AcquistionImage table row
			ctfdata - sinedon apCtfData table row
				amplitude constrast - ( a cos + sqrt(1-a^2) sin format)
				defocus1 > defocus2
				angle - in degrees, positive x-axis is zero
			outerbound = 5 #Angstrom resolution  (in meters)
				outside this radius is trimmed away
		"""
		### setup initial parameters for image
		#outerbound = outerbound * 2*math.sqrt(random.random())
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

		powerspec, self.trimfreq = ctftools.powerSpectraToOuterResolution(image, 
			outerbound*1e10, self.apix)
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
		normpowerspec = self.normalizeCtf(powerspec)
		if normpowerspec is None:
			return None

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
	#imagelist.extend(glob.glob("/data01/leginon/10apr19a/rawdata/10apr19a_10apr19a_*en_1.mrc")[:10])
	### Pick-wei images with lots of rings
	#imagelist.extend(glob.glob("/data01/leginon/09sep20a/rawdata/09*en.mrc")[:10])
	### Something else, ice data
	#imagelist.extend(glob.glob("/data01/leginon/09feb20d/rawdata/09*en.mrc")[:10])
	### OK groEL ice data
	#imagelist.extend(glob.glob("/data01/leginon/05may19a/rawdata/05*en*.mrc")[:10])
	### images of Hassan with 1.45/1.65 astig at various angles
	#imagelist.extend(glob.glob("/data01/leginon/12jun12a/rawdata/12jun12a_ctf_image_ang*.mrc")[:10])
	### rectangular images
	imagelist.extend(glob.glob("/data01/leginon/12may08eD1/rawdata/*.mrc")[:10])
	#=====================

	apDisplay.printMsg("# of images: %d"%(len(imagelist)))
	#imagelist.sort()
	#imagelist.reverse()
	random.shuffle(imagelist)
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

		ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata)
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ctffind")
		#ctfdata, bestconf = ctfdb.getBestCtfValueForImage(imgdata, method="ace2")
		if ctfdata is None:
			apDisplay.printColor("Skipping image %s, no CTF data"%(apDisplay.short(imagename)), "red")
			continue

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
def makeCtfImages(imgdata, ctfdata):
	a = CtfDisplay()
	ctfdisplaydict = a.CTFpowerspec(imgdata, ctfdata)
	return ctfdisplaydict



