#!/usr/bin/python -O

import sys
import os
import time
import data
import apXml
import apDisplay
import apDB
import apDatabase
import appionData
leginondb = apDB.db
appiondb = apDB.apdb

def defaults():
	params = {}
	params['numparticles']=3000
	params['numclasses']=40
	params['stackname']=None
	params['session']=None
	params['stackid']=None
	params['diam']=0
	params['bin']=1
	params['lp']=0
	params['outdir']=None
	params['mask']=None
	params['runid']=None

	return params

def cmdline(args, params):
	for arg in args:
		elem = arg.split("=")
		if elem[0] == "numpart":
			params['numparticles'] = int(elem[1])
		elif elem[0] == "numclass":
			params['numclasses'] = int(elem[1])
		elif elem[0] == "stackname":
			params['stackname'] = elem[1]
		elif elem[0] == "session":
			params['session'] = elem[1]
		elif elem[0] == "stackid":
			params['stackid'] = int(elem[1])
		elif elem[0] == "lp":
			params['lp'] = int(elem[1])
		elif elem[0] == "mask":
			params['mask'] = int(elem[1])
		elif elem[0] == "diam":
			params['diam'] = float(elem[1])
		elif elem[0] == "runid":
			params['runid'] = elem[1]
		elif elem[0] == "outdir":
			params['outdir'] = elem[1]
		else:
			apDisplay.printError("Unknown command: "+arg)

def conflicts(params):
	if params['runid'] is None:
		apDisplay.printError("Please provide a runid, example: runid=class1")
	return

def getStackId(params):
	if params['stackid'] is not None:
		return params['stackid']
	if params['session'] is None and params['stackname'] is None:
		apDisplay.printError("stack and session name undefined, please provide stack and session name."+\
			"\nexample: stackname=stack1 session=07jun05a")		
	if params['session'] is None:
		apDisplay.printError("session name undefined, please provide session name.\nexample: session=07jun05a")		
	if params['stackname'] is None:
		apDisplay.printError("stack name undefined, please provide stack name.\nexample: stackname=stack1")

	#checks done; find stackid
	stackq = appionData.ApStackParamsData()
	stackq['name'] = params['stackname']
	sessionid = apDatabase.getExpIdFromSessionName(params['session'])


def getStackInfo(params):
	#get the stack params
	stackdata = appiondb.direct_query(appionData.ApStackParamsData, params['stackid'])

	#get a stack particle params
	stackpartq = appionData.ApStackParticlesData()
	stackpartq['stackparams'] = stackdata
	stackpartdata = appiondb.query(stackpartq, results=1)[0]
	
	#get the particle normal params
	partdata = appiondb.direct_query(appionData.ApParticleData, stackpartdata['particle'].dbid)

	#get image params of the particle
	imgdata = leginondb.direct_query(data.AcquisitionImageData, partdata['dbemdata|AcquisitionImageData|image'])

	#set the parameters	
	params['session'] = imgdata['session']
	if stackdata['bin'] is not None:
		params['bin'] = stackdata['bin']
	params['apix'] = apDatabase.getPixelSize(imgdata)	
	params['stackpath'] = os.path.abspath(stackdata['stackPath'])
	if params['outdir'] is None:
		params['outdir'] = params['stackpath']
	params['stackfile'] = os.path.join(params['stackpath'],stackdata['name'])
	params['stacktype'] = stackdata['fileType']

	#apXml.fancyPrintDict(stackdata)
	#apXml.fancyPrintDict(stackpartdata)
	#apXml.fancyPrintDict(partdata)
	#apXml.fancyPrintDict(imgdata)

def createSpiderFile(params):
	"""
	takes the stack file and create a spider file ready for processing
	"""
	emancmd  = "proc2d "
	if not os.path.isfile(params['stackfile']):
		apDisplay.printError("stackfile does not exist: "+params['stackfile'])
	emancmd += params['stackfile']+" "
	emancmd += "startswapnorm.spi "
	emancmd += "apix="+str(params['apix'])+" "
	if params['lp'] > 0:
		emancmd += "lp="+str(params['lp'])+" "
	emancmd += "first=1 last="+str(params['numparticles'])+" "
	emancmd += "spiderswap "
	executeEmanCmd(emancmd)
	return

def averageTemplate(params):
	"""
	takes the spider file and creates an average template of all particles and masks it
	"""
	emancmd  = "proc2d startswapnorm.spi template.mrc average"
	executeEmanCmd(emancmd)
	emancmd  = "proc2d template.mrc template.mrc center"
	executeEmanCmd(emancmd)
	emancmd  = "proc2d template.mrc template.mrc mask="+str(params['mask'])
	executeEmanCmd(emancmd)

	time.sleep(2)
	return

def executeEmanCmd(emancmd):
	print emancmd

if __name__ == "__main__":
	params = defaults()
	cmdline(sys.argv[1:], params)
	conflicts(params)
	
	getStackInfo(params)
	os.chdir(params['outdir'])
	createSpiderFile(params)
	averageTemplate(params)
	
