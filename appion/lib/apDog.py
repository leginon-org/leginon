#Part of the new pyappion

import sys
import apDatabase,apDisplay
import apDB
import appionData
try:
	import libcv2
except:
	apDisplay.printError("cannot import libcv2, use a different machine")

partdb = apDB.apdb

def runDogDetector(imagename, params):
	#imgpath = img['session']['image path'] + '/' + imagename + '.mrc'
	#image = Mrc.mrc_to_numeric(imgpath)
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

def insertDogPicksIntoDB(img, peaks, params):
	sessionid = int(img['session'].dbid)
	imageid = int(img.dbid)
	presetid =int(img['preset'].dbid)
	bin = params['bin']

	print " ... inserting picks into database"

	for i in range(peaks.shape[0]):
		row = peaks[i,0] * bin
		col = peaks[i,1] * bin
		sca = peaks[i,2]

		runq = appionData.SelectionRunData()
		runq['name'] = params['id']+'_'+str(sca)
		runq['dbemdata|SessionData|session'] = sessionid

		particle = particleData.particle()
		particle['run'] = runq
		particle['image'] = imageid
		particle['selection'] = None
		particle['xcoord'] = col
		particle['ycoord'] = row
		#particle['slicenum'] = sca
		particle['correlation'] = sca
		partdb.insert(particle)
