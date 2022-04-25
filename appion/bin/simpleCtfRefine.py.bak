#!/usr/bin/env python

import os
import sys
import time
import math
import copy
import numpy
#import subprocess
from appionlib import apFile
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib.apCtf import ctftools, ctfdb
from appionlib.apCtf import genctf, ctfpower, ctfinsert
from appionlib.apImage import imagefilter
#Leginon
from pyami import mrc, primefactor
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

class RefineCTF(appionLoop2.AppionLoop):
	#====================================
	#====================================
	def setupParserOptions(self):
		### Input value options
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int",
			help="field size to use for sub-field averaging in power spectra calculation")

		self.parser.add_option("--ringwidth", dest="ringwidth", type="float", default=2.0,
			help="number of radial pixels to average during elliptical average")

		self.parser.add_option("--fast", dest="fast", default=False,
			action="store_true", help="Enable fast mode")

		self.parser.add_option("--reslimit", "--resolution-limit", dest="reslimit", type="float", default=6.0,
			help="outer resolution limit (in Angstroms) to clip the fft image")

		self.parser.add_option("--refineIter", dest="refineIter", type="int", default=130,
			help="maximum number of refinement interations")

		self.parser.add_option("--maxAmpCon", dest="maxAmpCon", type="float", default=0.25,
			help="maximum value allowed for amplitude contrast")

		self.parser.add_option("--minAmpCon", dest="minAmpCon", type="float", default=0.01,
			help="minimum value allowed for amplitude contrast")


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
		self.maxAmpCon = self.params['maxAmpCon']
		self.minAmpCon = self.params['minAmpCon']

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
			imgarray = imagefilter.correctImage(imgdata, self.params)
		else:
			imgarray = imgdata['image']

		### calculate power spectra
		apix = apDatabase.getPixelSize(imgdata)
		fftarray, freq = ctfpower.power(imgarray, apix, mask_radius=0.5, fieldsize=self.params['fieldsize'])
		#fftarray = imagefun.power(fftarray, mask_radius=1)

		fftarray = ndimage.median_filter(fftarray, 2)

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
	def printBestValues(self, ctfvalues):
		#if self.bestres > 200:
		#	return
		defocus = ctfvalues.get('defocus', 0)
		defastig = ctfvalues.get('defastig', 0)
		defangle = ctfvalues.get('defangle', 0)
		ampcont = ctfvalues.get('ampcont', 0)
		phase_shift = ctfvalues.get('phase_shift', 0)

		avgRes = self.bestres

		if defastig <= 0.0:
			apDisplay.printColor("Prev Best :: avgRes=%.4f :: def=%.3e, NO ASTIG, ampCon=%.3f"
				%(avgRes, defocus, ampcont), "gray")
		else:
			apDisplay.printColor("Prev Best :: avgRes=%.4f :: def=%.3e, defAstig=%.3e, ang=%.2f, ampCon=%.3f"
				%(avgRes, defocus, defastig, defangle, ampcont), "gray")
		return

	#====================================
	#====================================
	def xToCtfvalues(self, x):
		ctfvalues = {}
		xlist = list(x)
		if self.refine.get('phase_shift', False) is True:
			ctfvalues['phase_shift'] = xlist.pop()
		if self.refine.get('ampcont', False) is True:
			ctfvalues['ampcont'] = xlist.pop()
		if self.refine.get('defangle', False) is True:
			ctfvalues['defangle'] = xlist.pop()
		if self.refine.get('defastig', False) is True:
			ctfvalues['defastig'] = xlist.pop()
		if self.refine.get('defocus', False) is True:
			ctfvalues['defocus'] = xlist.pop()
		return ctfvalues

	#====================================
	#====================================
	def ctfvaluesToX(self, ctfvalues):
		x = []
		if self.refine.get('defocus', False) is True:
			x.append(ctfvalues['defocus'])
		if self.refine.get('defastig', False) is True:
			x.append(ctfvalues['defastig'])
		if self.refine.get('defangle', False) is True:
			x.append(ctfvalues['defangle'])
		if self.refine.get('ampcont', False) is True:
			x.append(ctfvalues['ampcont'])
		if self.refine.get('phase_shift', False) is True:
			x.append(ctfvalues['phase_shift'])
		return x

	#====================================
	#====================================
	def getCorrelation(self, ctfvalues):
		"""
		required self.ctfvalues must be filled
		"""
		## set local microscope values
		volts = self.ctfvalues['volts']
		cs = self.ctfvalues['cs']
		fftwidth = max(self.normPSD.shape)
		#TODO: this next value does not make sense, should be 1.0/xxxx
		mpix = 0.5/(fftwidth*self.mfreq)

		defocus = ctfvalues.get('defocus', self.ctfvalues['defocus'])
		defastig = ctfvalues.get('defastig', 0)
		defangle = ctfvalues.get('defangle', 0)
		ampcont = ctfvalues.get('ampcont', 0)
		phase_shift = ctfvalues.get('phase_shift', 0)

		if not (self.minAmpCon < ampcont < self.maxAmpCon):
			return 100.0
		if defastig < 0:
			return 100.0

		## set local ctf input values
		focus1 = (defocus - defastig/2.)*1e-6
		focus2 = (defocus + defastig/2.)*1e-6
		theta = math.radians(defangle) #theta is in radians

		## test parameters
		genctf.checkParams(focus1=focus1, focus2=focus2, pixelsize=mpix, cs=cs, volts=volts,
			ampconst=ampcont, extra_phase_shift=phase_shift, failParams=False)

		## generate ctf
		ctffitdata = genctf.generateCTF2d(focus1=focus1, focus2=focus2, theta=theta,
			shape=self.normPSD.shape, pixelsize=mpix, cs=cs, volts=volts, ampconst=ampcont,
			extra_phase_shift=phase_shift)

		ctffitdata *= self.hann
		mrc.write(self.normPSD, "normpsd.mrc")
		mrc.write(ctffitdata, "ctffitdata.mrc")
		mrc.write(ctffitdata*0.1+self.normPSD, "summed.mrc")

		#TODO: remove central part of the data

		correlation = scipy.stats.pearsonr(self.normPSD.ravel(), ctffitdata.ravel())[0]
		twocorr = correlation + 1

		reshack = 1.0/twocorr
		#print "%.6f, %.6f, %.6f"%(correlation, twocorr, reshack)

		if reshack < self.bestres:
			apDisplay.printColor("Congrats! Saving best resolution values %.3e and %.2f"
				%(defocus, ampcont), "green")
			self.bestres = reshack

		return reshack

	#====================================
	#====================================
	def boxNormalizeImage(self, PSD):
		t0 = time.time()

		imagedata = PSD.copy()
		boxsize = min(128, min(imagedata.shape)/10)
		boxfilter = ndimage.uniform_filter(imagedata, boxsize)
		normaldata = imagedata - boxfilter

		normaldata -= normaldata.min()
		normaldata /= numpy.abs(normaldata.max())

		apDisplay.printColor("Subtact 2D Box complete in %s"
			%(apDisplay.timeString(time.time()-t0)), "gray")

		return normaldata

	#====================================
	#====================================
	def refineMinFunc(self, x):
		ctfvalues = self.xToCtfvalues(x)
		#print ctfvalues
		avgres = self.getCorrelation(ctfvalues)
		self.fminCount += 1
		#ctfdb.getBestCtfByResolution(self.imgdata)
		self.printBestValues(ctfvalues)

		return avgres

	#====================================
	#====================================
	def refineLoop(self, fftarray):
		"""
		refines the following parameters, in order
			defocus
			amplitude contrast (mostly a dependent variable)
		"""
		self.fminCount = 0
		self.fftarray = fftarray

		### log file
		datafile = self.shortname+"-data.csv"
		self.datalog = open(datafile, "w")

		self.normPSD = self.boxNormalizeImage(self.fftarray)
		self.hann = ctfpower.twodHann(max(self.normPSD.shape))

		ctfvalues = {}
		ctfvalues['defocus'] = self.ctfvalues['defocus']*1e6
		ctfvalues['defastig'] = self.ctfvalues['defastig']*1e6
		ctfvalues['defangle'] = self.ctfvalues['angle_astigmatism']
		ctfvalues['ampcont'] = self.ctfvalues['amplitude_contrast']
		ctfvalues['phase_shift'] = self.ctfvalues.get('extra_phase_shift', 0)

		### create function self.refineMinFunc that would return res80+res50
		#x0 = [defocus, defastig, defangle, ampcont, phase_shift]
		x0 = self.ctfvaluesToX(ctfvalues)

		maxfun = self.params['refineIter']
		results = scipy.optimize.fmin(self.refineMinFunc, x0=x0, maxfun=maxfun)
		print "raw refine results =", results
		ctfvalues = self.xToCtfvalues(results)
		self.datalog.close()

		self.ctfvalues['defocus'] = ctfvalues.get('defocus', 0)*1e-6
		self.ctfvalues['defastig'] = ctfvalues.get('defastig', 0)*1e-6
		self.ctfvalues['angle_astigmatism'] = ctfvalues.get('defangle', 0)
		self.ctfvalues['amplitude_contrast'] = ctfvalues.get('amplitude_contrast', 0)
		self.ctfvalues['extra_phase_shift'] = ctfvalues.get('phase_shift', 0)

		self.printBestValues(ctfvalues)
		time.sleep(10)

	#====================================
	#====================================
	def runRefineCTF(self, imgdata, fftpath):
		### reset important values
		self.bestres = 1e10

		self.volts = imgdata['scope']['high tension']
		self.wavelength = ctftools.getTEMLambda(self.volts)
		## get value in meters
		self.cs = apInstrument.getCsValueFromSession(self.getSessionData())*1e-3
		self.ctfvalues = {
			'volts': self.volts,
			'wavelength': self.wavelength,
			'cs': self.cs,
		}

		### need to get FFT file open and freq of said file
		fftarray = mrc.read(fftpath).astype(numpy.float64)
		self.freq = self.freqdict[fftpath]

		### convert resolution limit into pixel distance
		fftwidth = fftarray.shape[0]
		maxres = 2.0/(self.freq*fftwidth)
		if maxres > self.params['reslimit']:
			apDisplay.printWarning("Cannot get requested res %.1fA higher than max Nyquist resolution %.1fA"
				%(self.params['reslimit'], maxres))
			self.params['reslimit'] = math.ceil(maxres*10)/10.

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
		self.origfftshape = fftarray.shape
		fftarray = imagefilter.frame_cut(fftarray, newshape)
		self.newfftshape = newshape

		### spacing parameters
		self.mfreq = self.freq*1e10
		fftwidth = min(fftarray.shape)
		self.apix = 1.0/(fftwidth*self.freq)
		self.ctfvalues['apix'] = self.apix

		### print message
		bestDbValues = ctfdb.getBestCtfByResolution(imgdata)
		self.shortname = apDisplay.short(imgdata['filename'])
		if bestDbValues is None:
			apDisplay.printColor("SKIPPING: No CTF values for image %s"
				%(apDisplay.short(imgdata['filename'])), "red")
			self.badprocess = True
			return

		### skip if resolution > 90.
		if bestDbValues['resolution_50_percent'] > 90.:
			apDisplay.printColor("SKIPPING: No decent CTF values for image %s"
				%(apDisplay.short(imgdata['filename'])), "yellow")
			self.badprocess = True
			return

		self.ctfvalues['amplitude_contrast'] = bestDbValues['amplitude_contrast']
		self.ctfvalues['defocus'] = (bestDbValues['defocus1'] + bestDbValues['defocus2'])/2.0
		self.ctfvalues['angle_astigmatism'] = bestDbValues['angle_astigmatism']
		self.ctfvalues['defastig'] = abs(bestDbValues['defocus2'] - bestDbValues['defocus1'])

		###
		#	This is the start of the actual program
		###
		self.refine = {
			'defocus': True,
			'defastig': True,
			'defangle': True,
			'ampcont': True,
			'phase_shift': False,
		}
		self.refineLoop(fftarray)

		##==================================
		## FINISH UP
		##==================================

		apDisplay.printColor("Finishing up using best found CTF values", "blue")

		### take best values and use them
		self.ctfvalues['defocus1'] = self.ctfvalues['defocus'] - self.ctfvalues['defastig']/2.
		self.ctfvalues['defocus2'] = self.ctfvalues['defocus'] + self.ctfvalues['defastig']/2.

		### stupid fix, get value in millimeters
		#self.ctfvalues['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())

		try:
			if self.ctfvalues['amplitude_contrast'] < self.minAmpCon:
				self.ctfvalues['amplitude_contrast'] = self.minAmpCon
			if self.ctfvalues['amplitude_contrast'] > self.maxAmpCon:
				self.ctfvalues['amplitude_contrast'] = self.maxAmpCon
		except KeyError:
			pass

		# get astig_angle within range -90 < angle <= 90
		while self.ctfvalues['angle_astigmatism'] > 90:
			self.ctfvalues['angle_astigmatism'] -= 180
		while self.ctfvalues['angle_astigmatism'] < -90:
			self.ctfvalues['angle_astigmatism'] += 180

		ctfvalues = {
			'defocus': self.ctfvalues['defocus']*1e6,
			'defastig': self.ctfvalues['defastig']*1e6,
			'defangle': self.ctfvalues['angle_astigmatism'],
			'ampcont': self.ctfvalues['amplitude_contrast'],
			'phase_shift': self.ctfvalues.get('extra_phase_shift', 0),
		}
		avgres = self.getCorrelation(ctfvalues)

		print "results =", (self.ctfvalues['defocus'], self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['amplitude_contrast'], avgres)

		apDisplay.printColor("Final defocus values %.3e -> %.3e, %.3e; ac=%.2f, res=%.1f"
			%(self.ctfvalues['defocus'], self.ctfvalues['defocus1'], self.ctfvalues['defocus2'],
			self.ctfvalues['amplitude_contrast'], avgres), "green")

		for i in range(10):
			print "===================================="

		print "PREVIOUS VALUES"
		ctfdb.getBestCtfByResolution(imgdata)
		print "CURRENT VALUES"
		defocusratio = self.ctfvalues['defocus2']/self.ctfvalues['defocus1']
		apDisplay.printColor("def1: %.2e | def2: %.2e | angle: %.1f | ampcontr %.2f | defratio %.3f"
			%(self.ctfvalues['defocus1'], self.ctfvalues['defocus2'], self.ctfvalues['angle_astigmatism'],
			self.ctfvalues['amplitude_contrast'], defocusratio), "blue")
		print "===================================="

		return

	#====================================
	#====================================
	def processImage(self, imgdata):
		### main function called by run
		self.ctfvalues = None
		fftpath = os.path.join(self.powerspecdir, apDisplay.short(imgdata['filename'])+'.powerspec.mrc')
		self.processAndSaveFFT(imgdata, fftpath)
		self.runRefineCTF(imgdata, fftpath)
		apFile.removeFile(fftpath)
		return

#====================================
#====================================
#====================================
if __name__ == '__main__':
	imgLoop = RefineCTF()
	imgLoop.run()

