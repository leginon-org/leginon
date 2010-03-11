#Part of the new pyappion

import sys
#import apDatabase
from appionlib import apDisplay
import math
import numpy
from appionlib import apImage
import pyami.quietscipy
from scipy import ndimage

def runDogDetector(imagename, params):
	"""
	This is an old libcv2 function that is no longer used
	"""
	#imgpath = img['session']['image path'] + '/' + imagename + '.mrc'
	#image = mrc.read(imgpath)
	#image = apDatabase.getImageData(imagename)['image']
	scale          = params['apix']
	if(params['binpixdiam'] != None):
		binpixrad      = params['binpixdiam']/2
	else:
		binpixrad      = params['diam']*params['apix']/float(params['bin'])/2.0
	search_range   = params['sizerange']
	sampling       = params['numslices']
	mintreshold    = params['minthresh']
	maxtreshold    = params['maxthresh']
	bin            = params['bin']

	sys.stderr.write(" ... running dog picker")
	try:
		import libcv2
	except:
		apDisplay.printError("cannot import libcv2, use a different machine")
	peaks = libcv2.dogDetector(image,bin,binpixrad,search_range,sampling,mintreshold,maxtreshold)
	print " ... done"

	return peaks

def convertDogPeaks(peaks, params):
	"""
	This is an old libcv2 function that is no longer used
	"""
	bin = params['bin']
	dictpeaks = []
	peak = {}
	for i in range(peaks.shape[0]):
		row = peaks[i,0] * bin
		col = peaks[i,1] * bin
		sca = peaks[i,2]
		peak['xcoord'] = col
		peak['ycoord'] = row
		peak['size']   = sca
		dictpeaks.append(peak.copy())
	return dictpeaks

def diffOfGaussParam(imgarray, params):
	apix = params['apix']
	bin = params['bin']
	diam = params['diam']
	k = params['kfactor']
	numslices = params['numslices']
	sizerange = params['sizerange']
	if diam == 0:
		apDisplay.printError("difference of Gaussian; radius = 0")
	pixrad = float(diam/apix/float(bin)/2.0)
	if numslices is None or numslices < 2:
		dogarray = diffOfGauss(imgarray, pixrad, k=k)
		dogarray = apImage.normStdev(dogarray)/4.0
		return [dogarray]
	else:
		pixrange = float(sizerange/apix/float(bin)/2.0)
		dogarrays, pixradlist = diffOfGaussLevels(imgarray, pixrad, numslices, pixrange)
		diamarray = numpy.asarray(pixradlist, dtype=numpy.float32) * apix * float(bin) * 2.0
		apDisplay.printColor("diameter list= "+str(numpy.around(diamarray,3)), "cyan")
		params['diamarray'] = diamarray
		return dogarrays

def diffOfGauss(imgarray0, pixrad, k=1.2):
	"""
	given bin, apix and diam of particle perform a difference of Gaussian
	about the size of that particle
	k := sloppiness coefficient
	"""
	# find xi (E) function of k
	Ek = math.sqrt( (k**2 - 1.0) / (2.0 * k**2 * math.log(k)) )
	# convert pixrad to sigma1
	sigma1 = Ek * pixrad
	# find sigmaprime
	sigmaprime = sigma1 * math.sqrt(k*k-1.0)
	#determine pixel range
	pixrange = pixrad * (k - 1.0) / math.sqrt(k)
	apDisplay.printMsg("filtering particles of size "+str(pixrad)+" +/- "
		+str(round(pixrange,1))+" pixels")
	#do the blurring
	imgarray1 = ndimage.gaussian_filter(imgarray0, sigma=sigma1)
	imgarray2 = ndimage.gaussian_filter(imgarray1, sigma=sigmaprime)
	#apImage.arrayToJpeg(imgarray1, "imgarray1.jpg")
	#apImage.arrayToJpeg(imgarray2, "imgarray2.jpg")
	dogmap = imgarray1-imgarray2
	apImage.arrayToJpeg(dogmap, "dogmap.jpg")
	return dogmap

def diffOfGaussLevels(imgarray, r0, N, dr, writeImg=False, apix=1):
	if writeImg is True:
		apImage.arrayToJpeg(imgarray, "binned-image.jpg")

	if dr >= 1.95*r0:
		apDisplay.printError("size range has be less than twice the diameter")

	# initial params
	#print "r0=", r0*apix
	#print "dr=", dr*apix
	#print "N=", N

	# find k based on info
	k = estimateKfactorIncrement(r0, dr, N)
	#print "k=", k
	# find xi (E) function of k
	Ek = math.sqrt( (k**2 - 1.0) / (2.0 * k**2 * math.log(k)) )
	##Ek = 1.0 / Ek
	#print "E(k)=", Ek
	# convert r0 to sigma1
	sigma1 = Ek * r0
	#print "sigma1=", sigma1*apix
	# find sigmaprime
	sigmaprime = sigma1 * math.sqrt(k**2 - 1.0)
	#print "sigma'=", sigmaprime*apix
	#sigma0 = sigma1 * k ^ (1-N)/2
	power = (float(1-N) / 2.0)
	#print "power=", power
	sigma0 = sigma1 * k**(float(1-N) / 2.0)
	#print "sigma0=", sigma0*apix

	# calculate first image blur
	sigma = sigma0
	gaussmap = ndimage.gaussian_filter(imgarray, sigma=sigma0)
	sigmavals = [sigma0,]
	sigprimes = []
	gaussmaps = [gaussmap,]
	for i in range(N):
		sigmaprime = sigma * math.sqrt(k**2 - 1.0)
		sigprimes.append(sigmaprime)
		#calculate new sigma
		sigma = math.sqrt( sigma**2 + sigmaprime**2 )
		sigmavals.append(sigma)
		# all subsequent blurs are by sigmaprime
		lastmap = gaussmaps[-1]
		gaussmap = ndimage.gaussian_filter(lastmap, sigma=sigmaprime)
		gaussmaps.append(gaussmap)

	#print "sigma' values=    ", numpy.array(sigprimes)*apix
	sizevals = numpy.array(sigmavals)/Ek/math.sqrt(k)*apix
	#print "map sigma sizes=  ", numpy.array(sigmavals)*apix
	sizevals = numpy.array(sigmavals)/Ek/math.sqrt(k)*apix
	#print "map central sizes=", sizevals
	sizevals = numpy.array(sigmavals)/Ek*apix
	#print "map pixel sizes=  ", sizevals[:-1]
	if writeImg is True:
		for i,gaussmap in enumerate(gaussmaps):
			apImage.arrayToJpeg(gaussmap, "gaussmap"+str(i)+".jpg")

	dogarrays = []
	pixradlist = []
	for i in range(N):
		pixrad = r0 * k**(float(i) - float(N-1) / 2.0)
		pixradlist.append(pixrad)
		# subtract blurs to get dog maps
		dogarray = gaussmaps[i] - gaussmaps[i+1]
		dogarray = apImage.normStdev(dogarray)/4.0
		dogarrays.append(dogarray)

		if writeImg is True:
			apImage.arrayToJpeg(dogarray, "dogmap"+str(i)+".jpg")

	sizevals = numpy.array(pixradlist)
	print "particle pixel sizes=", sizevals*apix

	#sys.exit(1)
	return dogarrays, sizevals

def estimateKfactorIncrement(r0, dr, N):
	dR = dr / ( 2.0 * r0 )
	powk = dR + math.sqrt( dR**2 + 1.0 )
	k = powk**(2.0/N)
	return k




