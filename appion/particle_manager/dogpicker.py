#!/usr/bin/python -O

import os, re, sys
import data
import time
import libcv2
import Mrc
import selexonFunctions  as sf1
import selexonFunctions2 as sf2
from selexonFunctions  import *
from selexonFunctions2 import *
import apLoop
import apParam


def modifyDefaultParams(params):
	#params={}
	params["ourdir"]="/tmp"
	params["apix"]=1
	params["diam"]=0
	params["bin"]=4
	params["range"]=0
	params["sample"]=1
	params["mint"]=3
	params["maxt"]=7
	params["sessionname"]=None
	params["preset"]=None
	params["id"]='picka_'
	params['commit']=False
	params['doneDictName'] = ".doneimages"
	return params

def dogHelp():
	print"""

dogpicker.py dbimages=<session>,<preset> diam=<particle_pixels> bin=<binning> range=<number_of_sizes> mint=<minimum_threshold_sigma> maxt=<maximum_threshold_sigma> id=<runid> [commit]

"""
	sys.exit()
	return()

def parseDogInput(args,params):

	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='bin'):
			params['bin']=float(elements[1])
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=float(elements[1])
		elif (elements[0]=='range'):
			params['range']=float(elements[1])
		elif (elements[0]=='sample'):
			params['sample']=float(elements[1])
		elif (elements[0]=='mint'):
			params["mint"]=float(elements[1])
		elif (elements[0]=='maxt'):
			params["maxt"]=float(elements[1])
		elif (elements[0]=='id'):
			params["id"]=elements[1]
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo) == 2:
				params['sessionname']=dbinfo[0]
				params['preset']=dbinfo[1]
			else:
				print "dbimages must include both session and preset parameters"
				sys.exit()
		elif (elements[0]=='commit'):
			params['commit']=True
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)

def runDogDetection(imagename, params):
	#imgpath = img['session']['image path'] + '/' + imagename + '.mrc'
	#image = Mrc.mrc_to_numeric(imgpath)
	image = sf1.getImageData(imagename)['image']

	scale          = params['apix']
	estimated_size = params['diam']/2
	search_range   = params['range']
	sampling       = params['sample']
	mintreshold    = params['mint']
	maxtreshold    = params['maxt']
	bin            = params['bin']

	peaks = libcv2.dogDetector(image,bin,estimated_size,search_range,sampling,mintreshold,maxtreshold)

	return peaks

if __name__ == '__main__':

	params=apParam.createDefaultParams()
	params=modifyDefaultParams(params)
	stats=apParam.createDefaultStats()

	if len(sys.argv) < 2:
		dogHelp()
	else:
		parseDogInput(sys.argv,params)
	
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

		peaks = runDogDetection(imagename, params)
		
		expid = int(img['session'].dbid)
		legimgid = int(img.dbid)
		legpresetid =int(img['preset'].dbid)
		
		if peaks is None:
			continue
		
		if params['commit']:
			print "Inserting picks into database"
			imgq = particleData.image()
			imgq['dbemdata|SessionData|session'] = expid
			imgq['dbemdata|AcquisitionImageData|image'] = legimgid
			imgq['dbemdata|PresetData|preset'] = legpresetid
			imgids = partdb.query(imgq,results=1)
			
			if not (imgids):
				partdb.insert(imgq)
				imgq=None
				imgq = particleData.image()
				imgq['dbemdata|SessionData|session']=expid
				imgq['dbemdata|AcquisitionImageData|image']=legimgid
				imgq['dbemdata|PresetData|preset']=legpresetid
				imgids=partdb.query(imgq, results=1)
			
			if not (imgids):
				continue
				
			for i in range(peaks.shape[0]):
				
				row = peaks[i,0] * bin
				col = peaks[i,1] * bin
				sca = peaks[i,2]
				
				runq=particleData.run()
				runq['name']=params['id']+'_'+str(sca)
				runq['dbemdata|SessionData|session']=expid
				
				particle = particleData.particle()
				particle['runId'] = runq
				particle['imageId'] = imgids[0]
				particle['selectionId'] = None
				particle['xcoord'] = col
				particle['ycoord'] = row
				particle['correlation'] = sca
				partdb.insert(particle)
			
		apLoop.printSummary(stats, params)

		print imagename + ' is done'
		apLoop.writeDoneDict(donedict,params,imagename)
