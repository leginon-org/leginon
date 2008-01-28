#Part of the new pyappion

import sys
#import apDatabase
import apDisplay
import math
import numpy
import apImage
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
	if numslices is None and numslices < 2:
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

def diffOfGauss(imgarray, pixrad, k=1.2):
	"""
	given bin, apix and diam of particle perform a difference of Gaussian
	about the size of that particle
	k := sloppiness coefficient
	"""
	#find k-factor
	kfact = math.sqrt( (k**2 - 1.0) / (2.0 * k**2 * math.log(k)) )
	# divide by sqrt(k) to span desired area 
	sigma1 = kfact * pixrad
	# divide by sqrt(k) to span desired area 
	sigma1 = sigma1 / math.sqrt(k)
	#sigma2 = k * sigma1 ==> sigmaDiff = 
	sigmaDiff = sigma1*math.sqrt(k*k-1.0)
	imgarray1 = ndimage.gaussian_filter(imgarray, sigma=sigma1)
	imgarray2 = ndimage.gaussian_filter(imgarray1, sigma=sigmaDiff)

	return imgarray2-imgarray1

def diffOfGaussLevels(imgarray, pixrad, numslices, pixrange):
	if pixrange >= 1.95*pixrad:
		apDisplay.printError("size range has be less than twice the diameter")

	#apDisplay.printError("This is method unfinished, remove the numslices and sizerange options")

	#get initial parameters
	kmult = estimateKfactorIncrement(pixrad, pixrange, numslices)
	kfact = math.sqrt( (kmult**2 - 1.0) / (2.0 * kmult**2 * math.log(kmult)) )
	sigma0 = kfact * pixrad

	#get two more slices than requested, since we are subtracting
	spower = -1.0 * float(numslices-1) / 2.0
	apDisplay.printMsg("s power: "+str(round(spower,3)))
	sigma1 = sigma0 * kmult**(spower)
	apDisplay.printMsg("sigma1: "+str(round(sigma1,3)))

	sigma = sigma1
	gaussmap = ndimage.gaussian_filter(imgarray, sigma=sigma)
	gaussmaps = [gaussmap,]
	sigmavals = [sigma,]
	for i in range(numslices):
		lastmap = gaussmaps[len(gaussmaps)-1]
		sigmaDiff = sigma*math.sqrt(kmult*kmult - 1.0)
		apDisplay.printMsg("sigmaDiff: "+str(round(sigmaDiff,3)))
		if sigmaDiff < 0.8:
			apDisplay.printWarning("sigma difference less than 0.8, reduce bin factor")
		sigma *= kmult
		sigmavals.append(sigma)
		gaussmap = ndimage.gaussian_filter(lastmap, sigma=sigmaDiff)
		gaussmaps.append(gaussmap)

	#print sigmavals
	#for i,gaussmap in enumerate(gaussmaps):
	#	apImage.arrayToJpeg(gaussmap, "gaussmap"+str(i)+".jpg")

	dogarrays = []
	pixradlist = []
	for i in range(numslices):
		dogarray = gaussmaps[i+1] - gaussmaps[i]
		pixradlist.append((sigmavals[i+1] + sigmavals[i])/2.0)
		dogarray = apImage.normStdev(dogarray)/4.0
		dogarrays.append(dogarray)
		#apImage.arrayToJpeg(dogarray, "dogmap"+str(i)+".jpg")

	#sys.exit(1)
	return dogarrays, pixradlist

def estimateKfactorIncrement(pixrad, pixrange, numslices):
	#lower bound estimate
	k1 = (1.0 - float(pixrange)/(2.0*float(pixrad)))**(-2.0/float(numslices-1))
	#upper bound estimate
	k2 = (1.0 + float(pixrange)/(2.0*float(pixrad)))**(2.0/float(numslices-1))
	#average both
	kavg = (k1 + k2)/2.0
	apDisplay.printMsg("mean k: "+str(round(kavg,3))+"; lower k: "+str(round(k1,3))+"; upper k: "+str(round(k2,3)))
	kerr = abs(k1 - k2)/(kavg - 1.0)
	#print kerr
	if kerr > 0.3:
		apDisplay.printWarning("large difference between upper and lower k values; selected range will not be inaccurate")

	return kavg
