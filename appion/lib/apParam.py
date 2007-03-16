#Part of the new pyappion

import os
import time
import mem
import re

def createDefaultParams():
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
	params['doneDictName'] = ".selexondone"
	return params

def createDefaultStats():
	stats={}
	stats["startTime"]=time.time()
	stats['count']  = 1
	stats['skipcount'] = 1
	stats['lastcount'] = 0
	stats['startmem'] = mem.used()
	stats['peaksum'] = 0
	stats['lastpeaks'] = None
	stats['imagesleft'] = 1
	stats['peaksumsq'] = 0
	stats['timesum'] = 0
	stats['timesumsq'] = 0
	stats['skipcount'] = 0
	stats['waittime'] = 0
	stats['lastimageskipped'] = False
	return stats

def parseCommandLineInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help' or args[1]=='--help' \
		or args[1]=='-h' or args[1]=='-help') :
		printSelexonHelp()

	lastarg=1

	# save the input parameters into the "params" dictionary

	# first get all images
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		elif (arg=='crudonly' or arg=='crud'):
			break
		else:
			mrcfile=arg
			mrcfileroot.append(os.path.splitext(mrcfile)[0])
		lastarg+=1
	params['mrcfileroot']=mrcfileroot

	# next get all selection parameters
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=float(elements[1])
		elif (elements[0]=='bin'):
			params['bin']=int(elements[1])
		elif (elements[0]=='range'):
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang']=int(angs[0])
				params['endang']=int(angs[1])
				params['incrang']=int(angs[2])
			else:
				print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
				sys.exit(1)
		elif (re.match('range\d+',elements[0])):
			num=elements[0][-1]
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang'+num]=int(angs[0])
				params['endang'+num]=int(angs[1])
				params['incrang'+num]=int(angs[2])
				params['multiple_range']=True
			else:
 				print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
				sys.exit(1)
		elif (elements[0]=='thresh'):
			params["thresh"]=float(elements[1])
		elif (elements[0]=='autopik'):
			params["autopik"]=float(elements[1])
		elif (elements[0]=='lp'):
			params["lp"]=float(elements[1])
		elif (elements[0]=='hp'):
			params["hp"]=float(elements[1])
		elif (elements[0]=='box'):
			params["box"]=int(elements[1])
		elif (arg=='crud'):
			params["crud"]=True
		elif (elements[0]=='cruddiam'):
			params["crud"]=True
			params["cdiam"]=float(elements[1])
		elif (elements[0]=='crudblur'):
			params["cblur"]=float(elements[1])
		elif (elements[0]=='crudlo'):
			params["clo"]=float(elements[1])
		elif (elements[0]=='crudhi'):
			params["chi"]=float(elements[1])
		elif (elements[0]=='crudstd'):
			params["cstd"]=float(elements[1])
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (arg=='crudonly'):
			params["crudonly"]=True
		elif (arg=='continue'):
			params["continue"]=True
		elif (elements[0]=='templateIds'):
			templatestring=elements[1].split(',')
			params['templateIds']=templatestring
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo) == 2:
				params['sessionname']=dbinfo[0]
				params['preset']=dbinfo[1]
				params["dbimages"]=True
				params["continue"]=True # continue should be on for dbimages option
			else:
				print "\nERROR: dbimages must include both \'session\' and \'preset\'"+\
					"parameters (ex: \'07feb13a,en\')\n"
				sys.exit(1)
		elif (elements[0]=='alldbimages'):
			params['sessionname']=elements[1]
			params['alldbimages']=True
		elif arg=='commit':
			params['commit']=True
		elif arg=='defocpair':
			params['defocpair']=True
		elif arg=='shiftonly':
			params['shiftonly']=True
		elif (elements[0]=='method'):
			params['method']=str(elements[1])
		elif (elements[0]=='overlapmult'):
			params['overlapmult']=float(elements[1])
		elif (elements[0]=='maxpeaks'):
			params['maxpeaks']=int(elements[1])
		elif (elements[0]=='crudschi'):
			params["cschi"]=float(elements[1])
		elif (elements[0]=='crudsclo'):
			params["csclo"]=float(elements[1])
		elif (elements[0]=='convolve'):
			params["convolve"]=float(elements[1])
		elif (elements[0]=='stdev'):
			params["stdev"]=float(elements[1])
		elif (arg=='no_hull'):
			params["no_hull"]=True
		elif (arg=='cv'):
			params["cv"]=True
			params["no_hull"]=True
		elif (arg=='no_length_prune'):
			params["no_length_prune"]=True
		elif (arg=='test'):
			params["test"]=True
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)

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
