#Part of the new pyappion

import sys
import apDatabase
import apDisplay
import apDB
import appionData

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


