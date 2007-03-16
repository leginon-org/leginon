#!/usr/bin/python -O

import sys
import data
import selexonFunctions  as sf1
#import selexonFunctions2 as sf2
#from selexonFunctions  import *
#from selexonFunctions2 import *
import apLoop
import apParam
import apDog

data.holdImages(False)

if __name__ == '__main__':

	apParam.writeFunctionLog(sys.argv,".dogpickerlog")
	params=apParam.createDefaultParams(function=sys.argv[0])
	params=apDog.modifyDefaultParams(params)
	stats=apParam.createDefaultStats()

	if len(sys.argv) < 2:
		apDog.dogHelp()
	else:
		apDog.parseDogInput(sys.argv,params)
	
	apParam.getOutDirs(params)

	#estimated_size = estimated_size / ( scale * bin )
	#search_range   =  search_range  / ( scale * bin )
	
	images=sf1.getImagesFromDB(params['sessionname'],params['preset'])
	stats['imagecount']=len(images)

	params['session']=images[0]['session']
	
	donedict=apLoop.readDoneDict(params)

	for img in images:
		
		imagename = img['filename']

		stats['imagesleft'] = stats['imagecount'] - stats['count']
		#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
		if( apLoop.startLoop(img, donedict, stats, params)==False ):
			continue

		peaks = apDog.runDogDetection(imagename, params)

		if peaks is None:
			continue
		
		numpeaks = (peaks.shape)[0]
		stats['lastpeaks'] = numpeaks
		stats['peaksum']   = stats['peaksum'] + numpeaks
		stats['peaksumsq'] = stats['peaksumsq'] + numpeaks**2

		expid = int(img['session'].dbid)
		legimgid = int(img.dbid)
		legpresetid =int(img['preset'].dbid)

		if params['commit']:
			print " ... inserting picks into database"
			imgq = sf1.particleData.image()
			imgq['dbemdata|SessionData|session'] = expid
			imgq['dbemdata|AcquisitionImageData|image'] = legimgid
			imgq['dbemdata|PresetData|preset'] = legpresetid
			imgids = sf1.partdb.query(imgq,results=1)
			
			if not (imgids):
				sf1.partdb.insert(imgq)
				imgq=None
				imgq = sf1.particleData.image()
				imgq['dbemdata|SessionData|session']=expid
				imgq['dbemdata|AcquisitionImageData|image']=legimgid
				imgq['dbemdata|PresetData|preset']=legpresetid
				imgids=sf1.partdb.query(imgq, results=1)
			
			if not (imgids):
				continue
				
			for i in range(peaks.shape[0]):
				
				row = peaks[i,0] * bin
				col = peaks[i,1] * bin
				sca = peaks[i,2]
				
				runq=particleData.run()
				runq['name']=params['id']+'_'+str(sca)
				runq['dbemdata|SessionData|session']=expid
				
				particle = sf1.particleData.particle()
				particle['runId'] = runq
				particle['imageId'] = imgids[0]
				particle['selectionId'] = None
				particle['xcoord'] = col
				particle['ycoord'] = row
				particle['correlation'] = sca
				partdb.insert(particle)
			
		apLoop.printSummary(stats, params)

		#print imagename + ' is done'
		apLoop.writeDoneDict(donedict,params,imagename)
	apLoop.completeLoop(stats)
