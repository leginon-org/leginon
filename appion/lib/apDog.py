#Part of the new pyappion

import sys
import apDatabase
import apDisplay
import apDB
import appionData
from scipy import ndimage

appiondb = apDB.apdb

def runDogDetector(imagename, params):
	#imgpath = img['session']['image path'] + '/' + imagename + '.mrc'
	#image = mrc.read(imgpath)
	image = apDatabase.getImageData(imagename)['image']
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

def convertDogPeaks(peaks,params):
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
	return diffOfGauss(imgarray, apix, bin, diam, k=k)

def diffOfGauss(imgarray, apix, bin, diam, k=1.2):
	"""
	given bin, apix and diam of particle perform a difference of Gaussian
	about the size of that particle
	k := sloppiness coefficient
	"""
	if diam == 0:
		apDisplay.printError("difference of Gaussian; radius = 0")
	pixrad = float(diam/apix/float(bin)/2.0)
	kfact = math.sqrt( (k**2 - 1.0) / (2.0 * k**2 * math.log(k)) )
	sigma1 = kfact * pixrad
	#sigma2 = k * sigma1
	sigmaD = math.sqrt(k*k-1.0)
	imgarray1 = ndimage.gaussian_filter(imgarray, sigma=sigma1)
	imgarray2 = ndimage.gaussian_filter(imgarray1, sigma=sigmaD)
	#kernel1 = convolver.gaussian_kernel(sigma1)
	#kernel2 = convolver.gaussian_kernel(sigmaD)
	#c=convolver.Convolver()
	#imgarray1 = c.convolve(image=imgarray,kernel=kernel1)
	#imgarray2 = c.convolve(image=imgarray1,kernel=kernelD)
	return imgarray2-imgarray1

def diffOfGaussLevels(imgarray, apix, bin, diam, numslices, sizerange):
	pixradlist = []
	for i in range(numslices):
		diamstep = sizerange/float(numslices)
		diammin = diam - sizerange/2.0
		diammax = diam + sizerange/2.0
		pixrad = float(diam/apix/float(bin)/2.0)
		pixradlist

	pixrad = float(diam/apix/float(bin)/2.0)




