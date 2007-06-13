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

def insertDogParams(params, expid):
	### query for identical params ###
	selexonparamsq = appionData.ApDogParamsData()
 	selexonparamsq['diam']=params['diam']
 	selexonparamsq['bin']=params['bin']
 	selexonparamsq['threshold']=params['thresh']
 	selexonparamsq['max_threshold']=params['maxthresh']
 	selexonparamsq['lp_filt']=params['lp']
 	selexonparamsq['hp_filt']=None
 	selexonparamsq['invert']=params['invert']
 	selexonparamsq['max_peaks']=params['maxpeaks']
	selexonparamsdata = appiondb.query(selexonparamsq, results=1)

	### query for identical run name ###
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid

	runids=appiondb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into dbappiondata
 	if not runids:
		apDisplay.printMsg("Inserting new runId into database")
		runq['dogparams'] = selexonparamsq
		if not selexonparamsdata:
			appiondb.insert(selexonparamsq)
		appiondb.insert(runq)

	return


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
		appiondb.insert(particle)
