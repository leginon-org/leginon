#!/usr/bin/env python


import math
import time
import numpy
#from scipy import signal
from scipy import stats
from scipy import ndimage
from scipy.stsci import convolve
#appion
from appionlib import apDog
from appionlib import apParam
from appionlib import apPeaks
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import particleLoop2
from appionlib.apImage import imagefile
from appionlib.apImage import imagestat
from appionlib.apImage import imagenorm
from appionlib.apImage import imagefilter
#pyami
from pyami import imagefun
#from pyami import correlator
from pyami import primefactor

class dogPicker(particleLoop2.ParticleLoop):
	#================
	def setupParserOptions(self):
		### Input value options
		self.parser.add_option("--kfactor", dest="kfactor", type="float", default=1.2,
			help="K-factor for the DoG picking algorithm", metavar="FLOAT")
		self.parser.add_option("--numslices", dest="numslices", type="int",
			help="Number of slices (different sizes) to pick", metavar="FLOAT")
		self.parser.add_option("--sizerange", dest="sizerange", type="float",
			help="Range in size of particles to find", metavar="FLOAT")

	#================
	def checkConflicts(self):
		if self.params['lowpass'] > 0:
			apDisplay.printWarning("lowpass filter value greater than zero; will ignore")
		if self.params['highpass'] > 0:
			apDisplay.printWarning("highpass filter value greater than zero; will ignore")
		self.params['highpass'] = None
		self.params['lowpass'] = None
		if self.params['numslices'] is not None and self.params['numslices'] >= 15:
			apDisplay.printError("too many slices defined by numslices, should be more like 2-6")
		if self.params['numslices'] > 1 and self.params['kfactor'] != 1.2:
			apDisplay.printWarning("k-factor is not used when numslices > 1")
		if self.params['diam'] < 1:
			apDisplay.printError("difference of Gaussian; radius = 0")
		if self.params['sizerange'] is not None and self.params['sizerange'] > 2*self.params['diam']-3:
			apDisplay.printError("size range %d has be less than twice the diameter %d"
				%(self.params['sizerange'], 2*self.params['diam']-3))
		### get number of processors:
		nproc = apParam.getNumProcessors()
		if not self.params['nproc']:
			self.params['nproc'] = nproc
		elif nproc < self.params['nproc']:
			apDisplay.printWarning("Limiting number of processors to the %i that are available"%nproc)
			self.params['nproc'] = nproc
		return

	#================
	def correlate(self, dogarray, pixrad):
		dogarray = imagenorm.normStdev(dogarray)
		#primefactor.maxprime = 5
		masksize = primefactor.getNextEvenPrime(pixrad*4 + 2)
		maskshape = (masksize, masksize)
		#print maskshape, pixrad
		maskimg = imagefun.filled_circle(maskshape, pixrad*1.25) - 2*imagefun.filled_circle(maskshape, pixrad) + 1
		#maskimg = 1 - imagefun.filled_circle(dogarray.shape, pixrad*2)
		#maskimg = imagefilter.tanhLowPassFilter(maskimg, 2)
		imagestat.printImageInfo(maskimg)
		maskimg = ndimage.gaussian_filter(maskimg, sigma=5, mode='constant', cval=0)
		#maskimg = imagenorm.normStdev(maskimg)

		t0 = time.time()
		apDisplay.printMsg("correlating...")
	
		#ccarray = signal.correlate2d(dogarray, maskimg)
		ccarray = convolve.correlate2d(dogarray, maskimg)

		#ccarray = convolve.correlate2d(maskimg, maskimg)
		#ccarray = imagefilter.frame_constant(ccarray, dogarray.shape)
		bigmask = imagefilter.frame_constant(maskimg, dogarray.shape)

		normval = math.sqrt( (dogarray**2).sum() * (bigmask**2).sum() )
		ccarray /= normval
		ccarray *= 30
		#ccarray /= ccarray.max()

		#normval = math.sqrt( (dogarray**2).sum() * (maskimg**2).sum() )/10
		ccval = stats.pearsonr(numpy.ravel(dogarray), numpy.ravel(bigmask))
		centerPixelValue = ccarray[ccarray.shape[0]/2, ccarray.shape[1]/2]
		normval = centerPixelValue / ccval[0]
		print "normval", normval, centerPixelValue, ccval[0]
		#ccarray = 2*imagenorm.normRange(ccarray) - 1

		print ccarray[ccarray.shape[0]/2, ccarray.shape[1]/2]

		#ccarray = feature.match_template(dogarray, maskimg)

		#import cv
		### convert from numpy format to openCV format
		#templateCv = cv.fromarray(numpy.float32(maskimg))
		#imageCv = cv.fromarray(numpy.float32(dogarray))
		### create array for storing result
		#resultCv =numpy.zeros(dogarray.shape, dtype=numpy.float32 )
		### perform normalized cross correlation
		#cv.MatchTemplate(templateCv, imageCv, resultCv, cv.CV_TM_CCORR_NORMED)
		### convert result back to numpy array
		#ccarray = np.asarray(resultCv)

		apDisplay.printMsg("done in %d seconds"%(time.time()-t0))
		#ccarray = numpy.fft.fftshift(ccarray)
		imagefile.arrayToJpeg(maskimg, "1maskimg.jpg")
		imagestat.printImageInfo(maskimg)
		imagefile.arrayToJpeg(dogarray, "2dogarray.jpg")
		imagestat.printImageInfo(dogarray)
		imagefile.arrayToJpeg(ccarray, "3ccarray.jpg")
		imagestat.printImageInfo(ccarray)
		print "\n\n"

		return ccarray

	#================
	def processImage(self, imgdata, filtarray):
		"""
		same as DoG Picker 1, but cross correlate size rather than use stdev
		"""
		pixrad = float(self.params['diam']/self.params['apix']/float(self.params['bin'])/2.0)
		apDisplay.printColor("central pixel radius = %.3f"%(pixrad), "cyan")
		if self.params['numslices'] is None or self.params['numslices'] < 2:
			apDisplay.printColor("diameter list= "+str(numpy.around(self.params['diam'],3)), "cyan")
			dogarray = apDog.diffOfGauss(filtarray, pixrad, k=self.params['kfactor'])
			ccarray = self.correlate(dogarray, pixrad)
			finalarrays = [ccarray]
		else:
			pixrange = float(self.params['sizerange']/self.params['apix']/float(self.params['bin'])/2.0)
			dogarrays, pixradlist = apDog.diffOfGaussLevels(filtarray, pixrad, self.params['numslices'], pixrange)
			finalarrays = []
			for i in range(len(pixradlist)):
				ccarray = self.correlate(dogarrays[i], pixradlist[i])
				finalarrays.append(ccarray)
			diamarray = numpy.asarray(pixradlist, dtype=numpy.float32) * self.params['apix'] * float(self.params['bin']) * 2.0
			apDisplay.printColor("diameter list= "+str(numpy.around(diamarray,3)), "cyan")
		imagestat.printImageInfo(finalarrays[0])
		time.sleep(1)
		peaktree  = apPeaks.findPeaks(imgdata, finalarrays, self.params, maptype="dogccmap")
		return peaktree

	#================
	def getParticleParamsData(self):
		dogparamq = appiondata.ApDogParamsData()
		dogparamq['kfactor'] = self.params['kfactor']
		dogparamq['size_range'] = self.params['sizerange']
		dogparamq['num_slices'] = self.params['numslices']
		return dogparamq

	#================
	def commitToDatabase(self, imgdata, rundata):
		return

if __name__ == '__main__':
	imgLoop = dogPicker()
	imgLoop.run()


