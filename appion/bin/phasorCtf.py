#!/usr/bin/env python

import os
import sys
import time
import math
import copy
import numpy
import random
from multiprocessing import Process
#import subprocess
from appionlib import apDog
from appionlib import apParam
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib.apCtf import ctftools, ctfnoise, ctfdb, sinefit, canny, findroots, findastig
from appionlib.apCtf import genctf, ctfpower, ctfres, ctfinsert, ransac, lowess, leastsq
from appionlib.apImage import imagefile, imagefilter, imagenorm, imagestat 
#Leginon
from pyami import mrc, fftfun, imagefun, ellipse, primefactor
from scipy import ndimage
import scipy.stats
import scipy.optimize

##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class PhasorCTF(appionLoop2.AppionLoop):
	#====================================
	#====================================
	def setupParserOptions(self):
		### Input value options
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int",
			help="field size to use for sub-field averaging in power spectra calculation")
		self.parser.add_option("--ringwidth", dest="ringwidth", type="float", default=2.0,
			help="number of radial pixels to average during elliptical average")

		self.parser.add_option("--reslimit", "--resolution-limit", dest="reslimit", type="float", default=6.0,
			help="outer resolution limit (in Angstroms) to clip the fft image")

		self.parser.add_option("--mindef", dest="mindef", type="float", default=0.5e-6,
			help="minimum defocus to search (in meters; default = 0.5e-6)")
		self.parser.add_option("--maxdef", dest="maxdef", type="float", default=5.0e-6,
			help="maximum defocus to search (in meters; default = 5.0e-6)")

		self.parser.add_option("--astig", dest="astig", default=True,
			action="store_true", help="Attempt to determine astigmatism")
		self.parser.add_option("--no-astig", dest="astig", default=True,
			action="store_false", help="Assume no astigmatism")

		self.parser.add_option("--refineIter", dest="refineIter", type="int", default=0,
			help="maximum number of refinement interations")

		self.parser.add_option("--fast", dest="fast", default=False,
			action="store_true", help="Enable fast mode")

		self.samples = ('stain','ice')
		self.parser.add_option("--sample", dest="sample",
			default="ice", type="choice", choices=self.samples,
			help="sample type: "+str(self.samples), metavar="TYPE")

	#====================================
	#====================================
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		if self.params['reslimit'] > 50 or self.params['reslimit'] < 1.0:
			apDisplay.printError("Resolution limit is in Angstroms")

		return

	#====================================
	#====================================
	def preLoopFunctions(self):
		## used for committing to database
		self.ctfrundata = None
		## used for each image
		self.ctfvalues = None
		## save freq (inverse pixel size) to a dict
		self.freqdict = {}
		## create opimages directory
		opdir = os.path.join(self.params['rundir'], "opimages")
		if not os.path.isdir(opdir):
			os.mkdir(opdir)
		self.powerspecdir =  os.path.join(self.params['rundir'], "powerspec")
		if not os.path.isdir(self.powerspecdir):
			os.mkdir(self.powerspecdir)
		self.readFreqFile()
		self.debug = False
		self.maxAmpCon = 0.25

	#====================================
	#====================================
	def processImage(self, imgdata):
		self.ctfvalues = None
		fftpath = os.path.join(self.powerspecdir, apDisplay.short(imgdata['filename'])+'.powerspec.mrc')
		self.processAndSaveFFT(imgdata, fftpath)
		self.runPhasorCTF(imgdata, fftpath)
		return

	#====================================
	#====================================
	def commitToDatabase(self, imgdata):
		"""
		information needed to commit
		* defocus 1
		* defocus 2
		* angle astig
		* amplitude contrast
		all stored in self.ctfvalues
		"""

		if ( not 'defocus1' in self.ctfvalues 
				or self.ctfvalues['defocus1'] is None
				or not 'defocus2' in self.ctfvalues
				or self.ctfvalues['defocus2'] is None
				or not 'amplitude_contrast' in self.ctfvalues
				or self.ctfvalues['amplitude_contrast'] is None
				or not 'angle_astigmatism' in self.ctfvalues
				or self.ctfvalues['angle_astigmatism'] is None):
			return False
		
		if self.ctfrundata is None:
			self.insertRunData()

		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrundata, self.params['rundir'])

		return True

	#====================================
	#====================================
	def insertRunData(self):
		runq=appiondata.ApAceRunData()
		runq['name']    = self.params['runname']
		runq['session'] = self.getSessionData()
		runq['hidden']  = False
		runq['path']    = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq.insert()
		self.ctfrundata = runq

	#====================================
	#====================================
	def reprocessImage(self, imgdata):
		"""
		Returns
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed
		e.g. a confidence less than 80%
		"""
		if self.params['reprocess'] is None:
			return True

		ctfvalue = ctfdb.getBestCtfByResolution(imgdata, msg=False)

		if ctfvalue is None:
			return None

		avgres = (ctfvalue['resolution_80_percent'] + ctfvalue['resolution_50_percent'])/2.0

		if avgres < self.params['reprocess']:
			return False
		return True

	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################

	#---------------------------------------
	def readFreqFile(self):
		self.freqfile = os.path.join(self.params['rundir'], "fft_frequencies.dat")
		self.freqdict = {}
		if os.path.isfile(self.freqfile):
			f = open(self.freqfile, "r")
			for line in f:
				sline = line.strip()
				if sline[0] == "#":
					continue
				bits = sline.split('\t')
				freq = float(bits[0].strip())
				fftpath = bits[1].strip()
				self.freqdict[fftpath] = freq
			f.close()
		apDisplay.printMsg("Read %d powerspec files from freqfile"%(len(self.freqdict)))
		return

	#---------------------------------------
	def saveFreqFile(self):
		if not self.freqdict:
			return
		f = open(self.freqfile, "w")
		f.write("#frequency	fft file\n")
		keys = self.freqdict.keys()
		keys.sort()
		for key in keys:
			f.write("%.8e\t%s\n"%(self.freqdict[key], key))
		f.close()
		return

	#---------------------------------------
	def processAndSaveFFT(self, imgdata, fftpath):
		if os.path.isfile(fftpath):
			print "FFT file found"
			if fftpath in self.freqdict.keys():
				print "Freq found"
				return False
			print "Freq not found"
		print "creating FFT file: ", fftpath

		### downsize and filter leginon image
		if self.params['uncorrected']:
			imgarray = imagefilter.correctImage(imgdata, params)
		else:
			imgarray = imgdata['image']

		### calculate power spectra
		apix = apDatabase.getPixelSize(imgdata)
		fftarray, freq = ctfpower.power(imgarray, apix, mask_radius=0.5, fieldsize=self.params['fieldsize'])
		#fftarray = imagefun.power(fftarray, mask_radius=1)

		fftarray = ndimage.median_filter(fftarray, 2)
		## temp fix
		#fftarray = ndimage.gaussian_filter(fftarray, 2)
		#fftarray = self.rotationBlur(fftarray, angle=2, numIter=3)

		## preform a rotational average and remove peaks
		rotfftarray = ctftools.rotationalAverage2D(fftarray)
		stdev = rotfftarray.std()
		rotplus = rotfftarray + stdev*4
		fftarray = numpy.where(fftarray > rotplus, rotfftarray, fftarray)

		### save to jpeg
		self.freqdict[fftpath] = freq
		mrc.write(fftarray, fftpath)

		self.saveFreqFile()

		return True

	#====================================
	#====================================
	def removeBlackCenter(self, raddata, PSDarray):
		#filter out central black circle
		cutval = max(PSDarray[:10].min(), 0.0) + 0.01
		args = numpy.where(PSDarray > cutval)[0]
		initarg = args[1]
		newraddata = raddata[initarg:]
		newPSDarray = PSDarray[initarg:]
		#print "SHAPE BABY", newraddata.shape, newPSDarray.shape
		return newraddata, newPSDarray

	#====================================
	#====================================
	def from2Dinto1D(self, fftarray):
		if self.params['astig'] is False and self.ellipseParams is None:
			### simple case: do a rotational average
			pixelrdata, PSDarray = ctftools.rotationalAverage(fftarray, self.params['ringwidth'], full=False)
			return self.removeBlackCenter(pixelrdata*self.freq, PSDarray)

		if self.ellipseParams is None:
			### hard case: find ellipse and do a elliptical average
			blurArray = copy.deepcopy(fftarray)
			for blurIter in range(2):
				### each time the image is blurred more
				blurArray = self.rotationBlur(blurArray, angle=1, numIter=3)
			self.findEllipseEdge(blurArray)
			if self.ellipseParams is None:
				apDisplay.printWarning("Failed to find ellipse, continuing with no astig")
				pixelrdata, PSDarray = ctftools.rotationalAverage(fftarray, self.params['ringwidth'], full=False)
				return self.removeBlackCenter(pixelrdata*self.freq, PSDarray)

		ellipratio = self.ellipseParams['a']/self.ellipseParams['b']
		ellipangle = math.degrees(self.ellipseParams['alpha'])
		pixelrdata, PSDarray = ctftools.ellipticalAverage(fftarray, ellipratio, ellipangle, 
			self.params['ringwidth'], full=False)
		return self.removeBlackCenter(pixelrdata*self.freq, PSDarray)

	#====================================
	#====================================
	def printBestValues(self):
		if self.bestres > 200:
			return
		avgRes = self.bestres/2.0
		defocus = self.bestvalues['defocus']
		ampCon = self.bestvalues['amplitude_contrast']
		if self.bestellipse is None:
			apDisplay.printColor("Prev Best :: avgRes=%.2f :: def=%.3e, NO ASTIG, ampCon=%.3f"
				%(avgRes, defocus, ampCon), "green")
		else:
			defratio = (self.bestellipse['a']/self.bestellipse['b'])**2
			angle = -math.degrees(self.bestellipse['alpha'])
			apDisplay.printColor("Prev Best :: avgRes=%.2f :: def=%.3e, defRatio=%.3f, ang=%.2f, ampCon=%.3f"
				%(avgRes, defocus, defratio, angle, ampCon), "green")
		return

	#====================================
	#====================================
	def getResolution(self, defocus, raddata, PSD, lowerBoundIndex, show=True):

		ctffitdata = genctf.generateCTF1d(raddata*1e10, focus=defocus, cs=self.ctfvalues['cs'],
			volts=self.ctfvalues['volts'], ampconst=self.ctfvalues['amplitude_contrast'], failParams=False)

		peaks = ctftools.getCtfExtrema(defocus, self.freq*1e10, self.ctfvalues['cs'], 
			self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'], numzeros=25, zerotype="peak")

		### get the confidence
		confraddata, confdata = ctfres.getCorrelationProfile(raddata, PSD, ctffitdata, peaks, self.freq)

		res5 = None
		res8 = None
		if confdata is not None and confdata.max() > self.maxAmpCon:
			res5 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.5)
			res8 = ctfres.getResolutionFromConf(confraddata, confdata, limit=0.8)

		if res8 is None:
			res8 = 100
		if res5 is None:
			res5 = 100

		if (res8+res5) < self.bestres and 0.0 < self.ctfvalues['amplitude_contrast'] < self.maxAmpCon:
			apDisplay.printColor("Congrats! Saving best resolution values %.3e and %.2f"
				%(defocus, self.ctfvalues['amplitude_contrast']), "green")
			self.bestres = (res8+res5)
			self.bestvalues = copy.deepcopy(self.ctfvalues)
			self.bestvalues['defocus'] = defocus
			self.bestellipse = copy.deepcopy(self.ellipseParams)
		elif show is True:
			print "not saving values %.2f, need an average better than %.2f"%((res8+res5), self.bestres)

		## normalize the data
		PSD -= (PSD[lowerBoundIndex:]).min()
		PSD /= numpy.abs(PSD[lowerBoundIndex:]).max()

		if self.debug is True and show is True:
			### Show the data
			raddatasq = raddata**2
			confraddatasq = confraddata**2
			peakradii = ctftools.getCtfExtrema(defocus, self.freq*1e10,
				self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
				numzeros=2, zerotype="peaks")
			firstpeak = peakradii[0]

			from matplotlib import pyplot
			pyplot.clf()
			### raw powerspectra data
			pyplot.plot(raddatasq[lowerBoundIndex:], PSD[lowerBoundIndex:], '-', color="red", alpha=0.5, linewidth=1)
			### ctf fit data
			pyplot.plot(raddatasq[lowerBoundIndex:], ctffitdata[lowerBoundIndex:], '-', color="black", alpha=0.5, linewidth=1)
			### confidence profile
			pyplot.plot(confraddatasq, confdata, '.', color="blue", alpha=0.9, markersize=10)
			pyplot.plot(confraddatasq, confdata, '-', color="blue", alpha=0.9, linewidth=2)

			pyplot.axvline(x=1/res8**2, linewidth=2, color="gold")
			pyplot.axvline(x=1/res5**2, linewidth=2, color="red")
		
			pyplot.title("Resolution values of %.3fA at 0.8 and %.3fA at 0.5"%(res8,res5))
			pyplot.xlim(xmin=raddatasq[lowerBoundIndex-1], xmax=raddatasq.max())
			pyplot.ylim(ymin=-0.05, ymax=1.05)
			pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
				bottom=0.05, left=0.05, top=0.95, right=0.95, )
			pyplot.show()

		apDisplay.printColor("Resolution values of %.4fA at 0.8 and %.4fA at 0.5"
			%(res8,res5), "magenta")

		return (res8+res5)/2.0

	#====================================
	#====================================
	def rotationBlur(self, imagedata, angle=1, numIter=2):
		t0 = time.time()
		if len(imagedata.shape) != 2:
			print "Must be 2D array for rotBlur"
			return imagedata

		arraylist = [imagedata,]
		for iterNum in range(numIter):
			rotateCounterClock = ndimage.interpolation.rotate(imagedata, iterNum*angle,
				order=1, mode='reflect', reshape=False)
			arraylist.append(rotateCounterClock)
      	
			rotateClock = ndimage.interpolation.rotate(imagedata, -iterNum*angle,
				order=1, mode='reflect', reshape=False)
			arraylist.append(rotateClock)

		rotblurdata = numpy.median(numpy.array(arraylist), axis=0)
		#print rotblurdata.shape
			
		if self.debug is True:
			apDisplay.printColor("Rotation blur complete in %s"
				%(apDisplay.timeString(time.time()-t0)), "cyan")
		return rotblurdata

	#====================================
	#====================================
	def fullTriSectionNormalize(self, raddata, PSD, defocus):
		t0 = time.time()

		### 
		### PART 1: BACKGROUND NOISE SUBTRACTION
		### 

		# skip the center
		valleys = ctftools.getCtfExtrema(defocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=250, zerotype="valleys")
		firstvalley = valleys[0]
		valleyradii = numpy.array(valleys, dtype=numpy.float64)*self.freq
		firstvalleyindex = numpy.searchsorted(raddata, self.freq*firstvalley)
		apDisplay.printColor("First valley: %.1f -> %d (1/%.1f A)"
			%(firstvalley, firstvalleyindex, 1/(firstvalley*self.freq)), "yellow")

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		numpoints = len(raddata) - firstvalleyindex
		npart1start = firstvalleyindex
		npart1end = int(firstvalleyindex + numpoints*6/10.)+1
		npart2start = int(firstvalleyindex + numpoints*5/10.)-1
		npart2end = int(firstvalleyindex + numpoints*9/10.)+1
		npart3start = int(firstvalleyindex + numpoints*8/10.)-1
		npart3end = len(raddata)

		apDisplay.printMsg("noise parts: %d-%d; %d-%d; %d-%d"
			%(npart1start, npart1end, npart2start, npart2end, npart3start, npart3end))

		if npart1start - npart3end < 5:
			apDisplay.printWarning("Not enough points for fullTriSectionNormalize")
			return PSD

		CtfNoise = ctfnoise.CtfNoise()
		if valleyradii is None:
			valleydata = ctfnoise.peakExtender(raddata, PSD, valleyradii, "below")
		else:
			valleydata = ndimage.minimum_filter(PSD, 4)

		## first part data
		noisefitparams1 = CtfNoise.modelCTFNoise(raddata[npart1start:npart1end],
			valleydata[npart1start:npart1end], "below")
		noisedata1 = CtfNoise.noiseModel(noisefitparams1, raddata)

		## second part data
		noisefitparams2 = CtfNoise.modelCTFNoise(raddata[npart2start:npart2end],
			valleydata[npart2start:npart2end], "below")
		noisedata2 = CtfNoise.noiseModel(noisefitparams2, raddata)

		## third part data
		noisefitparams3 = CtfNoise.modelCTFNoise(raddata[npart3start:npart3end],
			valleydata[npart3start:npart3end], "below")
		noisedata3 = CtfNoise.noiseModel(noisefitparams3, raddata)

		## merge data
		scale = numpy.arange(npart1end-npart2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = noisedata1[npart2start:npart1end]*(1-scale) + noisedata2[npart2start:npart1end]*scale
		scale = numpy.arange(npart2end-npart3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = noisedata2[npart3start:npart2end]*(1-scale) + noisedata3[npart3start:npart2end]*scale

		mergedata = numpy.hstack((noisedata1[:npart2start], overlapdata1,
			noisedata2[npart1end:npart3start], overlapdata2,
			noisedata3[npart2end:]))

		noisedata = mergedata

		### DO THE SUBTRACTION
		print PSD.shape, noisedata.shape
		if noisedata.shape[0] > PSD.shape[0]:
			noisedata = noisedata[:-1]
		print PSD.shape, noisedata.shape
		normexpPSD = numpy.exp(PSD) - numpy.exp(noisedata)
		normlogPSD = numpy.log(numpy.where(normexpPSD<1, 1, normexpPSD))

		### 
		### PART 2: ENVELOPE NORMALIZATION
		### 

		# high pass filter the center
		peaks = ctftools.getCtfExtrema(defocus, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], self.ctfvalues['amplitude_contrast'],
			numzeros=250, zerotype="peaks")
		firstpeak = peaks[0]
		peakradii = numpy.array(peaks, dtype=numpy.float64)*self.freq

		firstpeakindex = numpy.searchsorted(raddata, firstpeak*self.freq)
		apDisplay.printColor("First peak: %.1f (1/%.1f A)"%
			(firstpeakindex, 1/(firstpeak*self.freq)), "yellow")

		### split the function up in first 3/5 and last 3/5 of data with 1/5 overlap
		numpoints = len(raddata) - firstpeakindex
		epart1start = firstpeakindex
		epart1end = int(firstpeakindex + numpoints*6/10.)+1
		epart2start = int(firstpeakindex + numpoints*5/10.)-1
		epart2end = int(firstpeakindex + numpoints*9/10.)+1
		epart3start = int(firstpeakindex + numpoints*8/10.)-1
		epart3end = len(raddata)

		apDisplay.printMsg("exp parts: %d-%d; %d-%d; %d-%d"
			%(epart1start, epart1end, epart2start, epart2end, epart3start, epart3end))

		if epart1start - epart3end < 5:
			apDisplay.printWarning("Not enough points for fullTriSectionNormalize")
			return PSD

		CtfNoise = ctfnoise.CtfNoise()
		if peakradii is None:
			peakdata = ctfnoise.peakExtender(raddata, normlogPSD, peakradii, "above")
		else:
			peakdata = ndimage.maximum_filter(normlogPSD, 4)

		## first part data
		envelopfitparams1 = CtfNoise.modelCTFNoise(raddata[epart1start:epart1end],
			peakdata[epart1start:epart1end], "above")
		envelopdata1 = CtfNoise.noiseModel(envelopfitparams1, raddata)

		## second part data
		envelopfitparams2 = CtfNoise.modelCTFNoise(raddata[epart2start:epart2end],
			peakdata[epart2start:epart2end], "above")
		envelopdata2 = CtfNoise.noiseModel(envelopfitparams2, raddata)

		## third part data
		envelopfitparams3 = CtfNoise.modelCTFNoise(raddata[epart3start:epart3end],
			peakdata[epart3start:epart3end], "above")
		envelopdata3 = CtfNoise.noiseModel(envelopfitparams3, raddata)

		## merge data
		scale = numpy.arange(epart1end-epart2start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata1 = envelopdata1[epart2start:epart1end]*(1-scale) + envelopdata2[epart2start:epart1end]*scale
		scale = numpy.arange(epart2end-epart3start, dtype=numpy.float32)
		scale /= scale.max()
		overlapdata2 = envelopdata2[epart3start:epart2end]*(1-scale) + envelopdata3[epart3start:epart2end]*scale

		mergedata = numpy.hstack((envelopdata1[:epart2start], overlapdata1,
			envelopdata2[epart1end:epart3start], overlapdata2,
			envelopdata3[epart2end:]))
		envelopdata = mergedata

		### DO THE DIVISION
		print normexpPSD.shape, envelopdata.shape
		if envelopdata.shape[0] > normexpPSD.shape[0]:
			envelopdata = envelopdata[:-1]
		print normexpPSD.shape, envelopdata.shape
		normnormexpPSD = normexpPSD / numpy.exp(envelopdata)

		if self.debug is True:
			from matplotlib import pyplot
			pyplot.clf()
			pyplot.subplot(3,1,1)
			raddatasq = raddata**2
			pyplot.plot(raddatasq, normnormexpPSD, 'k.',)
			a = pyplot.plot(raddatasq, PSD, 'k-', alpha=0.5)
			a = pyplot.plot(raddatasq, valleydata, 'k-', alpha=0.5)
			b = pyplot.plot(raddatasq[firstvalleyindex:], noisedata[firstvalleyindex:], '--', color="purple", linewidth=2)
			c = pyplot.plot(raddatasq[npart1start:npart1end],
				noisedata1[npart1start:npart1end], 'b-', alpha=0.5, linewidth=2)
			d = pyplot.plot(raddatasq[npart2start:npart2end],
				noisedata2[npart2start:npart2end], 'r-', alpha=0.5, linewidth=2)
			e = pyplot.plot(raddatasq[npart3start:npart3end],
				noisedata3[npart3start:npart3end], '-', alpha=0.5, linewidth=2, color="green")
			pyplot.legend([a, b, c, d, e], ["data", "merge", "part 1", "part 2", "part 3"])
			pyplot.xlim(xmax=raddatasq.max())
			pyplot.ylim(ymin=noisedata.min(), ymax=PSD[npart1start:].max())

			pyplot.subplot(3,1,2)
			a = pyplot.plot(raddatasq, normlogPSD, 'k.',)
			a = pyplot.plot(raddatasq, normlogPSD, 'k-', alpha=0.5)
			a = pyplot.plot(raddatasq, peakdata, 'k-', alpha=0.5)
			b = pyplot.plot(raddatasq, mergedata, '--', color="purple", linewidth=2)
			c = pyplot.plot(raddatasq[epart1start:epart1end],
				envelopdata1[epart1start:epart1end], 'b-', alpha=0.5, linewidth=2)
			d = pyplot.plot(raddatasq[epart2start:epart2end],
				envelopdata2[epart2start:epart2end], 'r-', alpha=0.5, linewidth=2)
			e = pyplot.plot(raddatasq[epart3start:epart3end],
				envelopdata3[epart3start:epart3end], '-', alpha=0.5, linewidth=2, color="green")
			pyplot.legend([a, b, c, d, e], ["data", "merge", "part 1", "part 2", "part 3"])
			pyplot.xlim(xmax=raddatasq.max())
			pyplot.ylim(ymin=normlogPSD[epart1start:].min(), ymax=envelopdata.max())

			pyplot.subplot(3,1,3)
			pyplot.plot(raddatasq, normnormexpPSD, 'k.',)
			pyplot.plot(raddatasq, normnormexpPSD, 'k-', alpha=0.5)
			pyplot.xlim(xmax=raddatasq.max())

			pyplot.subplots_adjust(wspace=0.05, hspace=0.05,
				bottom=0.05, left=0.05, top=0.95, right=0.95, )
			pyplot.show()

		apDisplay.printColor("TriSection complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "cyan")

		return normnormexpPSD

	#====================================
	#====================================
	def findEllipseEdge(self, fftarray, mindef=None, maxdef=None):
		if mindef is None:
			mindef = self.params['mindef']
		if maxdef is None:
			maxdef = self.params['maxdef']

		minpeaks = ctftools.getCtfExtrema(maxdef, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], 0.0,
			numzeros=3, zerotype="peaks")
		minEdgeRadius = minpeaks[0]

		maxvalleys = ctftools.getCtfExtrema(mindef, self.freq*1e10,
			self.ctfvalues['cs'], self.ctfvalues['volts'], 0.0,
			numzeros=3, zerotype="valleys")

		minEdgeRadius = (maxvalleys[0]+minpeaks[0])/2
		maxEdgeRadius = maxvalleys[2]

		minCircum = math.ceil(2 * minEdgeRadius * math.pi)
		minEdges = int(minCircum)

		maxCircum = math.ceil(2 * maxEdgeRadius * math.pi)
		maxEdges = 2*int(maxCircum)

		dograd = (minpeaks[1] - minpeaks[0])/3.0
		dogarray = apDog.diffOfGauss(fftarray, dograd, k=1.2)
		#dogarray = fftarray

		print "Edge range: ", minEdges, maxEdges

		edges = canny.canny_edges(dogarray, low_thresh=0.01,
			minEdgeRadius=minEdgeRadius, maxEdgeRadius=maxEdgeRadius, minedges=minEdges, maxedges=maxEdges)
		#minedges=2500, maxedges=15000,
		invedges = numpy.fliplr(numpy.flipud(edges))
		self.edgeMap = numpy.logical_and(edges, invedges)
		edges = self.edgeMap * (dogarray.max()/self.edgeMap.max())
		imagedata = dogarray.copy() + edges
		imagefile.arrayToJpeg(imagedata, "edges.jpg")

		edgeThresh = 3
		ellipseParams = ransac.ellipseRANSAC(self.edgeMap, edgeThresh, maxRatio=self.maxRatio)
		if ellipseParams is None:
			return None

		fitEllipse1 = ransac.generateEllipseRangeMap2(ellipseParams, edgeThresh, self.edgeMap.shape)
		fitEllipse2 = ransac.generateEllipseRangeMap2(ellipseParams, edgeThresh*3, self.edgeMap.shape)
		outlineEllipse = fitEllipse2 - fitEllipse1
		# image is draw upside down
		#outlineEllipse = numpy.flipud(outlineEllipse)

		imagedata = imagedata + 0.5*outlineEllipse*imagedata.max()

		if self.debug is True:
			from matplotlib import pyplot
			pyplot.clf()
			pyplot.imshow(imagedata)
			pyplot.gray()
			pyplot.show()

		self.ellipseParams = ellipseParams

		#self.convertEllipseToCtf(node=3)

		return ellipseParams

	#====================================
	#====================================
	def fitLinearPlus(self, raddata, PSDarray):
		onevec = numpy.ones(raddata.shape)
		sqrtvec = numpy.sqrt(raddata)
		squarevec = raddata**2
		X = numpy.array([onevec, sqrtvec, raddata, squarevec]).transpose()
		fitparams = leastsq.totalLeastSquares(X, PSDarray, onevec)
		fitdata = fitparams[0] + fitparams[1]*sqrtvec + fitparams[2]*raddata + fitparams[3]*squarevec
		return fitdata

	#====================================
	#====================================
	def fitConstant(self, raddata, PSDarray):
		onevec = numpy.ones(raddata.shape)
		sqrtvec = numpy.sqrt(raddata)
		squarevec = raddata**2
		X = numpy.array([onevec]).transpose()
		fitparams = leastsq.totalLeastSquares(X, PSDarray, onevec)
		return fitparams[0]

	#====================================
	#====================================
	def gridSearch(self, raddata, PSDarray, lowerbound, mindef=None, maxdef=None):
		#location of first zero is linear with 1/sqrt(z)
		if mindef is None:
			mindef = self.params['mindef']
		if maxdef is None:
			maxdef = self.params['maxdef']

		maxVal = 1.0/math.sqrt(mindef)
		minVal = 1.0/math.sqrt(maxdef)
		randNum = (random.random() + random.random() + random.random()) / 3.0
		stepSize = 30 * randNum
		if self.params['fast'] is True:
			stepSize *= 2

		invGuesses = numpy.arange(minVal, maxVal, stepSize)
		random.shuffle(invGuesses)
		bestres = 1000.0
		oldampcontrast = self.ctfvalues['amplitude_contrast']
		resVals = []
		print "Guessing %d different defocus values"%(len(invGuesses))
		for invDefocus in invGuesses:
			defocus = 1.0/invDefocus**2
			ampcontrast = sinefit.refineAmplitudeContrast(raddata[lowerbound:]*1e10, defocus, 
				PSDarray[lowerbound:], self.ctfvalues['cs'], self.wavelength, msg=False)
			if ampcontrast is not None:
				self.ctfvalues['amplitude_contrast'] = ampcontrast
			avgres = self.getResolution(defocus, raddata, PSDarray, lowerbound, show=False)
			apDisplay.printColor("Def %.3e; Res %.1f"%(defocus, avgres), "red")
			resVals.append(avgres)
			if avgres < bestres:
				bestdef = defocus
				bestres = avgres
				avgres = self.getResolution(defocus, raddata, PSDarray, lowerbound, show=True)
		self.ctfvalues['amplitude_contrast'] = oldampcontrast

		if self.debug is True:
			from matplotlib import pyplot
			pyplot.clf()
			pyplot.plot(1.0e6/numpy.power(invGuesses,2), resVals, "o")
			#pyplot.axis('auto')
			#pyplot.ylim(ymin=5, ymax=80)
			pyplot.yscale('log')
			pyplot.show()

		return bestdef

	#====================================
	#====================================
	def defocusLoop(self, defocus, raddata, PSDarray, lowerbound, upperbound):
		avgres = self.getResolution(defocus, raddata, PSDarray, lowerbound)
		oldavgres = avgres*2
		newdefocus = defocus
		while avgres < oldavgres*0.99:
			newupperbound = numpy.searchsorted(raddata, 1.0/avgres)
			upperbound = max(newupperbound, upperbound)
			if avgres < oldavgres:
				oldavgres = avgres
			while lowerbound >= upperbound+1:
				print lowerbound, upperbound
				upperbound += 10
			if self.params['fast'] is True:
				mindef = 1.0/(1.01/math.sqrt(defocus))**2
				maxdef = 1.0/(0.99/math.sqrt(defocus))**2
			else:
				mindef = 1.0/(1.03/math.sqrt(defocus))**2
				maxdef = 1.0/(0.97/math.sqrt(defocus))**2
			newdefocus = self.gridSearch(raddata, PSDarray, lowerbound, mindef, maxdef)
			avgres = self.getResolution(newdefocus, raddata, PSDarray, lowerbound)
			results = sinefit.refineCTFOneDimension(raddata[lowerbound:upperbound]*1e10, 
				self.ctfvalues['amplitude_contrast'], newdefocus, PSDarray[lowerbound:upperbound], 
				self.ctfvalues['cs'], self.wavelength, msg=self.debug)
			if results is not None:
				self.ctfvalues['amplitude_contrast'] = results[0]
				newdefocus = results[1]
			avgres = self.getResolution(newdefocus, raddata, PSDarray, lowerbound)
			if avgres > self.bestres:
				defocus = newdefocus
		self.printBestValues()
		return self.fixAmpContrast(defocus, raddata, PSDarray, lowerbound, upperbound)

	#====================================
	#====================================
	def fixAmpContrast(self, defocus, raddata, PSDarray, lowerbound, upperbound):
		if self.ctfvalues['amplitude_contrast'] > 0 and self.ctfvalues['amplitude_contrast'] < self.maxAmpCon:
			return defocus
		bad = True
		newdefocus = defocus
		count = 0
		while count < 20:
			count += 1
			amplitudecontrast = sinefit.refineAmplitudeContrast(raddata[lowerbound:upperbound]*1e10, newdefocus, 
				PSDarray[lowerbound:upperbound], self.ctfvalues['cs'], self.wavelength, msg=self.debug)
			if amplitudecontrast is None:
				apDisplay.printWarning("FAILED to fix amplitude contrast")
				return defocus
			elif amplitudecontrast < 0:
				apDisplay.printColor("Amp Cont: %.3f too small, decrease defocus %.3e"%
					(amplitudecontrast, newdefocus), "blue")
				scaleFactor = 0.999 - abs(amplitudecontrast)/5.
				newdefocus = newdefocus*scaleFactor
			elif amplitudecontrast > self.maxAmpCon:
				apDisplay.printColor("Amp Cont: %.3f too large, increase defocus %.3e"%
					(amplitudecontrast, newdefocus), "cyan")
				scaleFactor = 1.001 + abs(amplitudecontrast - self.maxAmpCon)/5.
				newdefocus = newdefocus*scaleFactor
			else:
				apDisplay.printColor("Amp Cont: %.3f in range!!!  defocus %.3e"%
					(amplitudecontrast, newdefocus), "green")
				avgres = self.getResolution(newdefocus, raddata, PSDarray, lowerbound)
				self.ctfvalues['amplitude_contrast'] = amplitudecontrast
				return newdefocus

			avgres = self.getResolution(newdefocus, raddata, PSDarray, lowerbound)
			if avgres < self.bestres:
				defocus = newdefocus
		apDisplay.printWarning("FAILED to fix amplitude contrast")
		return defocus

	#====================================
	#====================================
	def findEllipseLoop(self, fftarray, lowerbound, upperbound):

		blurArray = copy.deepcopy(fftarray)

		numIter = 5
		if self.params['fast'] is True:
			numIter = 2

		for blurIter in range(5):
			### each time the image is blurred more
			blurArray = self.rotationBlur(blurArray, angle=1, numIter=3)
			blurArray = ndimage.gaussian_filter(blurArray, 2)

			### edge find method
			if self.bestvalues is None:
				return
			defocus = self.bestvalues['defocus']
			#follows 1/sqrt(z) rule:
			mindef = 1.0/(1.02/math.sqrt(defocus))**2
			maxdef = 1.0/(0.98/math.sqrt(defocus))**2
			self.findEllipseEdge(blurArray, mindef=mindef, maxdef=maxdef)
			raddata, PSDarray = self.from2Dinto1D(blurArray)
			normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)
			defocus = self.defocusLoop(defocus, raddata, normPSDarray, lowerbound, upperbound)
			normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)
			defocus = self.defocusLoop(defocus, raddata, normPSDarray, lowerbound, upperbound)

			### minimum valley method
			defocus = self.bestvalues['defocus']
			ellipseParams = findastig.findAstigmatism(blurArray, self.freq, defocus, 0, self.ctfvalues)
			if ellipseParams is not None:
				ellipRatio = ellipseParams['a']/ellipseParams['b']
				if 1.0/self.maxRatio < ellipRatio < self.maxRatio:
					self.ellipseParams = ellipseParams
					raddata, PSDarray = self.from2Dinto1D(blurArray)
					normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)
					defocus = self.defocusLoop(defocus, raddata, normPSDarray, lowerbound, upperbound)
					normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)
					defocus = self.defocusLoop(defocus, raddata, normPSDarray, lowerbound, upperbound)

			if self.params['fast'] is True:
				continue

			### minimum valley method
			defocus = self.bestvalues['defocus']
			ellipseParams = findastig.findAstigmatism(blurArray, self.freq, defocus, 0, self.ctfvalues, peakNum=2)
			if ellipseParams is not None:
				ellipRatio = ellipseParams['a']/ellipseParams['b']
				if 1.0/self.maxRatio < ellipRatio < self.maxRatio:
					self.ellipseParams = ellipseParams
					raddata, PSDarray = self.from2Dinto1D(blurArray)
					normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)
					defocus = self.defocusLoop(defocus, raddata, normPSDarray, lowerbound, upperbound)
					normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)
					defocus = self.defocusLoop(defocus, raddata, normPSDarray, lowerbound, upperbound)
	
			self.printBestValues()

	#====================================
	#====================================
	def refineMinFunc(self, x):
		ellipRatio, ellipAlpha = x

		self.ellipseParams['b'] = self.ellipseParams['a']/ellipRatio
		self.ellipseParams['alpha'] = ellipAlpha
		defocus = self.bestvalues['defocus']

		raddata, PSDarray = self.from2Dinto1D(self.fftarray)
		normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)
		defocus = self.defocusLoop(self.bestvalues['defocus'], raddata, normPSDarray, self.lowerbound, self.upperbound)
		avgres = self.getResolution(defocus, raddata, normPSDarray, self.lowerbound, show=False)
		for i in range(4):
			print "********"
		self.fminCount += 1
		#ctfdb.getBestCtfByResolution(self.imgdata)
		self.printBestValues()
		apDisplay.printColor(
			"FMIN :: defRatio=%.3f < a=%.1f , d=%.2e == %.2fA (%d)"
				%(ellipRatio**2, -math.degrees(ellipAlpha), defocus, avgres, self.fminCount),
			"cyan")
		return avgres

	#====================================
	#====================================
	def refineEllipseLoop(self, fftarray, lowerbound, upperbound):
		"""
		refines the following parameters, in order
			ellipRatio
			ellipAngle
			defocus
			amplitude contrast (mostly a dependent variable)
		"""
		if self.params['refineIter'] <= 0:
			return

		self.fminCount = 0
		### "self.ellipseParams" controls what self.from2Dinto1D() does
		ellipRatio = self.ellipseParams['a']/self.ellipseParams['b']
		ellipAlpha = self.ellipseParams['alpha']
		origEllipParams = copy.deepcopy(self.ellipseParams)
		self.fftarray = fftarray	
		self.lowerbound = lowerbound
		self.upperbound = upperbound

		### create function self.refineMinFunc that would return res80+res50
		x0 = [ellipRatio, ellipAlpha]
		maxfun = self.params['refineIter']
		results = scipy.optimize.fmin(self.refineMinFunc, x0=x0, maxfun=maxfun)

		ellipRatio, ellipAlpha = results
		apDisplay.printColor("BEST FROM FMIN :: defRatio=%.3f < a=%.2f"
			%(ellipRatio**2, -math.degrees(ellipAlpha)), "blue")

		self.printBestValues()
		time.sleep(10)

	#====================================
	#====================================
	def runPhasorCTF(self, imgdata, fftpath):
		### reset important values
		self.bestres = 1e10
		self.bestellipse = None
		self.bestvalues = None
		self.ellipseParams = None
		self.volts = imgdata['scope']['high tension']
		self.wavelength = ctftools.getTEMLambda(self.volts)
		## get value in meters
		self.cs = apInstrument.getCsValueFromSession(self.getSessionData())*1e-3
		self.ctfvalues = {
			'volts': self.volts,
			'wavelength': self.wavelength,
			'cs': self.cs,
		}

		if self.params['astig'] is False:
			self.maxRatio=1.3
		else:
			self.maxRatio=2.0

		### need to get FFT file open and freq of said file
		fftarray = mrc.read(fftpath).astype(numpy.float64)
		self.freq = self.freqdict[fftpath]

		### print message
		ctfdb.getBestCtfByResolution(imgdata)

		### convert resolution limit into pixel distance
		fftwidth = fftarray.shape[0]
		maxres = 2.0/(self.freq*fftwidth)
		if maxres > self.params['reslimit']:
			apDisplay.printError("Cannot get requested res %.1fA higher than max res %.1fA"
				%(maxres, self.params['reslimit']))

		limitwidth = int(math.ceil(2.0/(self.params['reslimit']*self.freq)))
		limitwidth = primefactor.getNextEvenPrime(limitwidth)
		requestres = 2.0/(self.freq*limitwidth)
		if limitwidth > fftwidth:
			apDisplay.printError("Cannot get requested resolution"
				+(" request res %.1fA higher than max res %.1fA for new widths %d > %d"
				%(requestres, maxres, limitwidth, fftwidth)))

		apDisplay.printColor("Requested resolution OK: "
			+(" request res %.1fA less than max res %.1fA with fft widths %d < %d"
			%(requestres, maxres, limitwidth, fftwidth)), "green")
		newshape = (limitwidth, limitwidth)
		fftarray = imagefilter.frame_cut(fftarray, newshape)

		### spacing parameters
		self.mfreq = self.freq*1e10
		fftwidth = min(fftarray.shape)
		self.apix = 1.0/(fftwidth*self.freq)
		self.ctfvalues['apix'] = self.apix

		if self.params['sample'] is 'stain':
			self.ctfvalues['amplitude_contrast'] = 0.14
		else:
			self.ctfvalues['amplitude_contrast'] = 0.07

		###
		#	This is the start of the actual program
		###

		### this is either simple rotational average, 
		### or complex elliptical average with edge find and RANSAC
		raddata, PSDarray = self.from2Dinto1D(fftarray)

		lowerrad = ctftools.getCtfExtrema(self.params['maxdef'], self.mfreq, self.cs, self.volts, 
			self.ctfvalues['amplitude_contrast'], 1, "valley")
		lowerbound = numpy.searchsorted(raddata, lowerrad[0]*self.freq)

		if self.params['sample'] is 'stain':
			upperbound = numpy.searchsorted(raddata, 1/8.)
		else:
			upperbound = numpy.searchsorted(raddata, 1/12.)

		### fun way to get initial defocus estimate
		fitData = self.fitLinearPlus(raddata, PSDarray)
		#lowessFit = lowess.lowess(raddata**2, PSDarray, smoothing=0.6666)

		if self.debug is True:
			from matplotlib import pyplot
			pyplot.clf()
			pyplot.plot(raddata**2, PSDarray)
			pyplot.plot(raddata**2, fitData)
			pyplot.show()

		flatPSDarray = PSDarray-fitData
		flatPSDarray /= numpy.abs(flatPSDarray[lowerbound:upperbound]).max()

		defocus = self.gridSearch(raddata, flatPSDarray, lowerbound)

		#defocus = findroots.estimateDefocus(raddata[lowerbound:upperbound], flatPSDarray[lowerbound:upperbound], 
		#	cs=self.cs, wavelength=self.wavelength,  amp_con=self.ctfvalues['amplitude_contrast'], 
		#	mindef=self.params['mindef'], maxdef=self.params['maxdef'], volts=self.volts)
	
		amplitudecontrast = sinefit.refineAmplitudeContrast(raddata[lowerbound:upperbound]*1e10, defocus, 
			flatPSDarray[lowerbound:upperbound], self.ctfvalues['cs'], self.wavelength, msg=self.debug)
		if amplitudecontrast is not None:
			print "amplitudecontrast", amplitudecontrast
			self.ctfvalues['amplitude_contrast'] = amplitudecontrast
	
		defocus = self.defocusLoop(defocus, raddata, flatPSDarray, lowerbound, upperbound)

		#lowerrad = ctftools.getCtfExtrema(defocus, self.mfreq, self.cs, self.volts, 
		#	self.ctfvalues['amplitude_contrast'], 1, "valley")
		#lowerbound = numpy.searchsorted(raddata, lowerrad[0]*self.freq)

		normPSDarray = self.fullTriSectionNormalize(raddata, PSDarray, defocus)

		defocus = self.defocusLoop(defocus, raddata, normPSDarray, lowerbound, upperbound)

		self.findEllipseLoop(fftarray, lowerbound, upperbound)

		self.refineEllipseLoop(fftarray, lowerbound, upperbound)

		##==================================
		## FINISH UP
		##==================================

		apDisplay.printColor("Finishing up using best found CTF values", "blue")
		self.printBestValues()

		if self.bestvalues is None:
			apDisplay.printColor("No CTF estimate found for this image", "red")	
			self.badprocess = True
			return

		### take best values and use them
		self.ctfvalues = self.bestvalues
		self.ellipseParams = self.bestellipse

		### stupid fix, get value in millimeters
		self.ctfvalues['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())

		### translate ellipse into ctf values
		if self.ellipseParams is not None:
			self.ctfvalues['angle_astigmatism'] = math.degrees(self.ellipseParams['alpha'])
			ellipratio = self.ellipseParams['a']/self.ellipseParams['b']
			phi = math.asin(self.ctfvalues['amplitude_contrast'])
			#note: a > b then def1 < def2
			#major axis
			self.ctfvalues['defocus1'] = self.ctfvalues['defocus']/ellipratio
			#minor axis
			self.ctfvalues['defocus2'] = self.ctfvalues['defocus']*ellipratio

			defdiff = 1.0 - 2*self.ctfvalues['defocus']/(self.ctfvalues['defocus1']+self.ctfvalues['defocus2'])
			print "%.3e --> %.3e,%.3e"%(self.ctfvalues['defocus'], 
					self.ctfvalues['defocus2'], self.ctfvalues['defocus1'])
			print defdiff*100
			if defdiff*100 > 1:
				apDisplay.printWarning("Large astigmatism")
				#sys.exit(1)
		else:
			self.ctfvalues['angle_astigmatism'] = 0.0
			self.ctfvalues['defocus1'] = self.ctfvalues['defocus']
			self.ctfvalues['defocus2'] = self.ctfvalues['defocus']

		if self.ctfvalues['amplitude_contrast'] < 0.0:
			self.ctfvalues['amplitude_contrast'] = 0.0
		if self.ctfvalues['amplitude_contrast'] > self.maxAmpCon:
			self.ctfvalues['amplitude_contrast'] = self.maxAmpCon

		if abs(self.ctfvalues['defocus1']) > abs(self.ctfvalues['defocus2']):
			# incorrect, need to shift angle by 90 degrees
			apDisplay.printWarning("|def1| > |def2|, flipping defocus axes")
			tempdef = self.ctfvalues['defocus1']
			self.ctfvalues['defocus1'] = self.ctfvalues['defocus2']
			self.ctfvalues['defocus2'] = tempdef
			self.ctfvalues['angle_astigmatism'] += 90
		# get astig_angle within range -90 < angle <= 90
		while self.ctfvalues['angle_astigmatism'] > 90:
			self.ctfvalues['angle_astigmatism'] -= 180
		while self.ctfvalues['angle_astigmatism'] < -90:
			self.ctfvalues['angle_astigmatism'] += 180

		avgres = self.getResolution(self.ctfvalues['defocus'], raddata, PSDarray, lowerbound)
		apDisplay.printColor("Final defocus values %.3e -> %.3e, %.3e; ac=%.2f, res=%.1f"
			%(self.ctfvalues['defocus'], self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['amplitude_contrast'], avgres/2.0), "green")

		for i in range(10):
			print "===================================="

		print "PREVIOUS VALUES"
		ctfdb.getBestCtfByResolution(imgdata)
		print "CURRENT VALUES"
		defocusratio = self.ctfvalues['defocus2']/self.ctfvalues['defocus1']
		apDisplay.printColor("def1: %.2e | def2: %.2e | angle: %.1f | ampcontr %.2f | defratio %.3f"
			%(self.ctfvalues['defocus1'], self.ctfvalues['defocus2'], self.ctfvalues['angle_astigmatism'],
			self.ctfvalues['amplitude_contrast'], defocusratio), "blue")
		self.printBestValues()
		print "===================================="

		return

#====================================
#====================================
#====================================
if __name__ == '__main__':
	imgLoop = PhasorCTF()
	imgLoop.run()

