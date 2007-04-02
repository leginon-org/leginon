#Part of the new pyappion

import sys
import apDatabase,apDisplay
import particleData
import dbdatakeeper
try:
	import libcv2
except:
	apDisplay.printError("cannot import libcv2, use a different machine")

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

def insertDogPicksIntoDB(img, peaks, params):
	partdb = dbdatakeeper.DBDataKeeper(db='dbparticledata')
	sessionid = int(img['session'].dbid)
	imageid = int(img.dbid)
	presetid =int(img['preset'].dbid)
	bin = params['bin']

	print " ... inserting picks into database"
	imgq = particleData.image()
	imgq['dbemdata|SessionData|session'] = sessionid
	imgq['dbemdata|AcquisitionImageData|image'] = imageid
	imgq['dbemdata|PresetData|preset'] = presetid
	imgids = partdb.query(imgq,results=1)
	
	# failed, create new entry
	if not (imgids):
		partdb.insert(imgq)
		imgq = None
		imgq = particleData.image()
		imgq['dbemdata|SessionData|session']=sessionid
		imgq['dbemdata|AcquisitionImageData|image']=imageid
		imgq['dbemdata|PresetData|preset']=presetid
		imgids=partdb.query(imgq, results=1)

	#double fail
	if not (imgids):
		return
		
	for i in range(peaks.shape[0]):
		row = peaks[i,0] * bin
		col = peaks[i,1] * bin
		sca = peaks[i,2]

		runq = particleData.run()
		runq['name'] = params['id']+'_'+str(sca)
		runq['dbemdata|SessionData|session'] = sessionid

		particle = particleData.particle()
		particle['runId'] = runq
		particle['imageId'] = imgids[0]
		particle['selectionId'] = None
		particle['xcoord'] = col
		particle['ycoord'] = row
		#particle['slicenum'] = sca
		particle['correlation'] = sca
		partdb.insert(particle)
