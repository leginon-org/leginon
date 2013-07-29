#!/usr/bin/env python

import os
import wx
import sys
import time
import math
import copy
import numpy
from multiprocessing import Process
#import subprocess
from appionlib import apDog
from appionlib import apParam
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib.apCtf import ctftools, ctfnoise, ctfdb, sinefit, canny, findroots
from appionlib.apCtf import genctf, ctfpower, ctfres, ctfinsert, ransac, lowess
from appionlib.apImage import imagefile, imagefilter, imagenorm, imagestat
#Leginon
from pyami import mrc, fftfun, imagefun, ellipse, primefactor
from scipy import ndimage
import scipy.stats

##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class LsqCTF(appionLoop2.AppionLoop):

	#====================================
	def setupParserOptions(self):
		### Input value options
		self.parser.add_option("--shape", dest="shape", default='+',
			help="pick shape")
		self.parser.add_option("--shapesize", dest="shapesize", type="int", default=16,
			help="shape size")
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int",
			help="field size to use for sub-field averaging in power spectra calculation")
		self.parser.add_option("--reslimit", "--resolution-limit", dest="reslimit", type="float", default=6.0,
			help="outer resolution limit (in Angstroms) to clip the fft image")
		self.parser.add_option("--ringwidth", dest="ringwidth", type="float", default=2.0,
			help="number of radial pixels to average during elliptical average")
		self.parser.add_option("--mindef", dest="mindef", type="float", default=0.5e-6,
			help="minimum defocus to search (in meters; default = 0.5e-6)")
		self.parser.add_option("--maxdef", dest="maxdef", type="float", default=5.0e-6,
			help="maximum defocus to search (in meters; default = 5.0e-6)")

		self.parser.add_option("--astig", dest="astig", default=True,
			action="store_true", help="Attempt to determine astigmatism")
		self.parser.add_option("--no-astig", dest="astig", default=True,
			action="store_false", help="Assume no astigmatism")

		self.samples = ('stain','ice')
		self.parser.add_option("--sample", dest="sample",
			default="ice", type="choice", choices=self.samples,
			help="sample type: "+str(self.samples), metavar="TYPE")


	#====================================
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""
		if self.params['reslimit'] > 50 or self.params['reslimit'] < 1.0:
			apDisplay.printError("Resolution limit is in Angstroms")

		return

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

	#====================================
	def processImage(self, imgdata):
		self.ctfvalues = None
		fftpath = os.path.join(self.powerspecdir, apDisplay.short(imgdata['filename'])+'.powerspec.mrc')
		self.processAndSaveFFT(imgdata, fftpath)
		self.runLsqCTF(imgdata, fftpath)
		return

	#====================================
	def commitToDatabase(self, imgdata):
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

		if self.params['projectid'] == 13 or self.params['projectid'] == 15:
			print "wrong project"
			sys.exit(1)

		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrundata, self.params['rundir'])
		return True

	#====================================
	def insertRunData(self):
		runq=appiondata.ApAceRunData()
		runq['name']    = self.params['runname']
		runq['session'] = self.getSessionData()
		runq['hidden']  = False
		runq['path']    = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq.insert()
		self.ctfrundata = runq

	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################

	#====================================
	def processAndSaveFFT(self, imgdata, fftpath):
		if os.path.isfile(fftpath) and fftpath in self.freqdict.keys():
			return False

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

		## preform a rotational average to remove spikes
		rotfftarray = ctftools.rotationalAverage2D(fftarray)
		stdev = rotfftarray.std()
		rotplus = rotfftarray + stdev*4
		fftarray = numpy.where(fftarray > rotplus, rotfftarray, fftarray)

		### save to jpeg
		self.freqdict[fftpath] = freq
		mrc.write(fftarray, fftpath)
		return True

	#====================================
	def from2Dinto1D(self, fftarray):
		if self.params['astig'] is False:
			### simple case: do a rotational average
			pixelrdata, PSDarray = ctftools.rotationalAverage(fftarray, self.params['ringwidth'], full=False)
			raddata = pixelrdata*self.freq
			#filter out central black circle
			cutval = max(PSDarray[:10].min(), 0.0) + 0.01
			args = numpy.where(PSDarray > cutval)[0]
			args = args[1:]
			raddata = raddata[args]
			PSDarray = PSDarray[args]
			return raddata, PSDarray
		else:
			### hard case: find ellipse and do a elliptical average
			raise NotImplementedError

	#====================================
	def runLsqCTF(self, imgdata, fftpath):
		### need to get FFT file open and freq of said file
		fftarray = mrc.read(fftpath).astype(numpy.float64)
		freq = self.freqdict[fftpath]

		### convert resolution limit into pixel distance
		fftwidth = fftarray.shape[0]
		maxres = 2.0/(freq*fftwidth)
		if maxres > self.params['reslimit']:
			apDisplay.printError("Cannot get requested res %.1fA higher than max res %.1fA"
				%(maxres, self.params['reslimit']))

		limitwidth = int(math.ceil(2.0/(self.params['reslimit']*freq)))
		limitwidth = primefactor.getNextEvenPrime(limitwidth)
		requestres = 2.0/(freq*limitwidth)
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
		self.freq = freq
		fftwidth = min(fftarray.shape)
		self.apix = 1.0/(fftwidth*freq)

		self.volts = imgdata['scope']['high tension']
		self.wavelength = ctftools.getTEMLambda(self.volts)
		self.cs = apInstrument.getCsValueFromSession(self.getSessionData())*1e-3
		self.ctfvalues = {
			'volts': self.volts,
			'wavelength': self.wavelength,
			'cs': self.cs,
			'apix': self.apix,
		}

		if self.params['sample'] is 'stain':
			self.ctfvalues['amplitude_contrast'] = 0.14
		else:
			self.ctfvalues['amplitude_contrast'] = 0.07

		raddata, PSDarray = self.from2Dinto1D(fftarray)
		lowessFit = lowess.lowess(raddata, PSDarray, smoothing=0.4)
		
		newzavg = findroots.estimateDefocus(raddata, PSDarray-lowessFit, cs=self.cs, wavelength=self.wavelength, 
			amp_con=self.ctfvalues['amplitude_contrast'], mindef=self.params['mindef'], maxdef=self.params['maxdef'])

		from matplotlib import pyplot
		pyplot.clf()
		pyplot.plot(raddata, PSDarray)
		pyplot.plot(raddata, lowessFit)
		pyplot.show()

		pyplot.clf()
		pyplot.plot(raddata, PSDarray-lowessFit)
		pyplot.show()

		sys.exit(1)

		return

#====================================
#====================================
if __name__ == '__main__':
	imgLoop = LsqCTF()
	imgLoop.run()

