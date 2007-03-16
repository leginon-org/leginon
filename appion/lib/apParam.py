#Part of the new pyappion

import os
import time
import mem

def createDefaults():
	# create default values for parameters
	params={}
	params["mrcfileroot"]=''
	params["template"]=''
	params["templatelist"]=[]
	params["apix"]=None
	params["diam"]=0
	params["bin"]=4
	params["startang"]=0
	params["endang"]=10
	params["incrang"]=20
	params["thresh"]=0.5
	params["autopik"]=0
	params["lp"]=30
	params["hp"]=600
	params["box"]=0
	params["crud"]=False
	params["cdiam"]=0
	params["cblur"]=3.5
	params["clo"]=0.6
	params["chi"]=0.95
	params["cstd"]=1
	params["crudonly"]=False
	params["continue"]=False
	params["multiple_range"]=False
	params["dbimages"]=False
	params["alldbimages"]=False
	params["session"]=None
	params["preset"]=None
	params["runid"]='run1'
	params["commit"]=False
	params["defocpair"]=False
	params["abspath"]=os.path.abspath('.')+'/'
	params["shiftonly"]=False
	params["templateIds"]=''
	params["ogTmpltInfo"]=[]
	params["scaledapix"]={}
	params["outdir"]=None
	params['description']=None
	params['scale']=1
	params['projectId']=None
	params['prtltype']=None
	params['method']="updated"
	params['overlapmult']=1.5
	params['maxpeaks']=1500
	params["cschi"]=1
	params["csclo"]=0
	params["convolve"]=0
	params["no_hull"]=False
	params["cv"]=False
	params["no_length_prune"]=False
	params["stdev"]=0
	params["test"]=False
	notdone=True
	params["startTime"]=time.time()
	params['count']  = 1
	params['skipcount'] = 1
	params['lastcount'] = 0
	params['startmem'] = mem.used()
	params['peaksum'] = 0
	params['lastpeaks'] = None
	params['imagesleft'] = 1
	params['peaksumsq'] = 0
	params['timesum'] = 0
	params['timesumsq'] = 0
	params['doneDictName'] = ".selexondone"
	params['skipcount'] = 0
	params['waittime'] = 0
	params['lastimageskipped'] = False
	return params

def checkParamConflicts(params):
	if not params['templateIds'] and not params['apix']:
		print "\nERROR: if not using templateIds, you must enter a template pixel size\n"
		sys.exit(1)
	if params['templateIds'] and params['template']:
		print "\nERROR: Both template database IDs and mrc file templates are specified,\nChoose only one\n"
		sys.exit(1)
	if params['crudonly']==True and params['shiftonly']==True:
		print "\nERROR: crudonly and shiftonly can not be specified at the same time\n"
		sys.exit(1)
	if (params["thresh"]==0 and params["autopik"]==0):
		print "\nERROR: neither manual threshold or autopik parameters are set, please set one.\n"
		sys.exit(1)
	if (params["diam"]==0):
		print "\nERROR: please input the diameter of your particle\n"
		sys.exit(1)
	if len(params["mrcfileroot"]) > 0 and params["dbimages"]==True:
		print params['imagecount']
		print "\nERROR: dbimages can not be specified if particular images have been specified\n"
		sys.exit(1)
	if params['alldbimages'] and params['dbimages']==True:
		print "\nERROR: dbimages and alldbimages can not be specified at the same time\n"
		sys.exit(1)
	if len(params['mrcfileroot']) > 0 and params['alldbimages']:
		print "\nERROR: alldbimages can not be specified if particular images have been specified\n"
		sys.exit(1)
