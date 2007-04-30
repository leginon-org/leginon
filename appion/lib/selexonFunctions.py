#!/usr/bin/python -O
# Python functions for selexon.py

#python lib
import os, re, sys
import cPickle
import math
import string
import time
#numarray
import numarray
import numarray.convolve as convolve
import numarray.nd_image as nd_image
#leginon
import data
import convolver
import Mrc
import imagefun
import peakfinder
import correlator
import project
#appion
#import particleData
import appionData
import apDisplay
import apDB
import apTemplate
import apImage
import apDatabase
import apParticle

db = apDB.db
partdb = apDB.apdb
projdb = apDB.projdb


def createDefaults():
	apDisplay.printWarning("this apParam function should not be in use")
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
	return params

def printUploadHelp():
	print "\nUsage:\nuploadTemplate.py template=<name> apix=<pixel> session=<session> [commit]\n"
	print "selexon template=groEL apix=1.63 session=06nov10a commit\n"
	print "template=<name>      : name should not have the extension, or number."
	print "                       groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>         : angstroms per pixel (unbinned)"
	print "diam=<n>             : approximate diameter of particle (in Angstroms, unbinned)"
	print "session=<sessionId>  : session name associated with template (i.e. 06mar12a)"
	print "description=\"text\"   : description of the template - must be in quotes"
	print "\n"

	sys.exit(1)

def printPrtlUploadHelp():
	print "\nUsage:\nuploadParticles.py <boxfiles> scale=<n>\n"
	print "selexon *.box scale=2\n"
	print "<boxfiles>            : EMAN box file(s) containing picked particle coordinates"
	print "runid=<runid>         : name associated with these picked particles (default is 'manual1')"
	print "scale=<n>             : If particles were picked on binned images, enter the binning factor"
	print "\n"

	sys.exit(1)

def printSelexonHelp():
	print "\nUsage:\nselexon.py <file> template=<name> apix=<pixel> diam=<n> bin=<n> [templateIds=<n,n,n,n,...>] [range=<start,stop,incr>] [thresh=<threshold> or autopik=<n>] [lp=<n>] [hp=<n>] [crud or cruddiam=<n>] [crudonly] [crudblur=<n>] [crudlow=<n>] [crudhi=<n>] [box=<n>] [continue] [dbimages=<session>,<preset>] [alldbimages=<session>] [commit] [defocpair] [shiftonly] [outdir=<path>] [method=<method>] [overlapmult=<n>]"
	print "Examples:\nselexon 05jun23a_00001en.mrc template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud"
	print "selexon template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud dbimages=05jun23a,en continue\n"
	print "template=<name>    : name should not have the extension, or number."
	print "                     groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>       : angstroms per pixel (unbinned)"
	print "diam=<n>           : approximate diameter of particle (in Angstroms, unbinned)"
	print "bin=<n>            : images will be binned by this amount (default is 4)"
	print "range=<st,end,i>   : each template will be rotated from the starting angle to the"
	print "                     stop angle at the given increment"
	print "                     User can also specify ranges for each template (i.e. range1=0,60,20)"
	print "                     NOTE: if you don't want to rotate the image, leave this parameter out"
	print "thresh=<thr>       : manual cutoff for correlation peaks (0-1), don't use if want autopik (default is 0.5)"
	print "autopik=<thr>      : automatically calculate threshold, n = average number of particles per image"
	print "                     NOTE: autopik does NOT work for *updated* method"
	print "lp=<n>, hp=<n>     : low-pass and high-pass filter (in Angstroms) - (defaults are 30 & 600)"
	print "                     NOTE: high-pass filtering is currently disabled"
	print "crud               : run the crud finder after the particle selection"
	print "                     (will use particle diameter by default)"
	print "cruddiam=<n>       : set the diameter to use for the crud finder"
	print "                     (don't need to use the \"crud\" option if using this)"
	print "crudblur=<n>       : amount to blur the image for edge detection (default is 3.5 binned_pixels)"
	print "crudlo=<n>         : lower limit for edge detection (0-1, default=0.6)"
	print "crudhi=<n>         : upper threshold for edge detection (0-1, default=0.95)"
	print "crudstd=<n>        : lower limit for scaling the edge detection limits (i.e. stdev of the image) (default=1= never scale)"
	print "crudonly           : only run the crud finder to check and view the settings"
	print "box=<n>            : output will be saved as EMAN box file with given box size"
	print "continue           : if this option is turned on, selexon will skip previously processed"
	print "                     micrographs"
	print "commit             : if commit is specified, particles will be stored to the database (not implemented yet)"
	print "dbimages=<sess,pr> : if this option is turned on, selexon will continuously get images from the database"
	print "alldbimages=<sess> : if this option is turned on selexon will query the database for all images"
	print "                     associated with the session"
	print "runid=<runid>      : subdirectory for output (default=run1)"
	print "                     do not use this option if you are specifying particular images"
	print "defocpair          : calculate shift between defocus pairs"
	print "shiftonly          : skip particle picking and only calculate shifts"
	print "templateIds        : list the database id's of the templates to use"
	print "outdir=<path>      : output directory in which results will be written"
	print "method=<method>    : choices: classic, updated (default), and experimental"
	print "                       classic - calls findem and viewit"
	print "                       updated - uses findem and internally find peaks (default)"
	print "                       experimental - internally generates cc maps and find peaks"
	print "overlapmult=<n>    : distance multiple for two particles to overlap (default is 1.5 X)"
	print "maxpeaks=<n>       : maximum number of particles allowed per image"
	print "crudschi=<n>               : image standard deviation hi limit for scaling the edge detection limits (default=1: use crudhi&crudlo)"
	print "crudsclo=<n>               : image standard deviation lower limit for scaling the edge detection limits (default=0: use crudhi&crudlo)"
	print "convolve=<n>               : if not zero, convolve the thresholded edge blobs with a disk at the particle diameter to unify blobs"
	print "                             and then threshold it at <n> fraction of peak self covolution of the disk (0-1, default=0"
	print "no_hull                    : if ON, convex hull is not calculated"
	print "cv                         : if ON, polygon vertices are calculated us libCV"
	print "no_length_prune            : if ON, pruning by crud perimeters is not done before convex hull"
	print "stdev=<n>                  : if not zero, only regions with stdev larger than n*image_stdev is passed (default=0)"
	print "test                       : if ON, images at each step are saved"
	print "\n"

	sys.exit(1)

def parseUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printUploadHelp()

	# save the input parameters into the "params" dictionary
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		elif (elements[0]=='session'):
			params['session']=elements[1]
		elif (elements[0]=='description'):
			params['description']=elements[1]
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

def parsePrtlUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printPrtlUploadHelp()

	lastarg=1
	
	# first get all box files
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		else:
			boxfile=arg
			if (os.path.exists(boxfile)):
				# in case of multiple extenstions, such as pik files
				splitfname=(os.path.basename(boxfile).split('.'))
				mrcfileroot.append(splitfname[0])
				params['extension']=string.join(splitfname[1:],'.')
				params['prtltype']=splitfname[-1]
			else:
				apDisplay.printError("file \'"+boxfile+"\' does not exist \n")
		lastarg+=1
	params["imgs"]=mrcfileroot

	# save the input parameters into the "params" dictionary
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='scale'):
			params['scale']=int(elements[1])
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		else:
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")

def parseSelexonInput(args,params):
	apDisplay.printError("this apParam function is no longer in use")
	"""
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
				apDisplay.printError("\'range\' must include 3 angle parameters: start, stop, & increment\n")
		elif (re.match('range\d+',elements[0])):
			num = re.sub("range(?P<num>[0-9]+)","\g<num>",elements[0])
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang'+num]=int(angs[0])
				params['endang'+num]=int(angs[1])
				params['incrang'+num]=int(angs[2])
				params['multiple_range']=True
			else:
 				apDisplay.printError("\'range\' must include 3 angle parameters: start, stop, & increment\n")
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
				params['session']=dbinfo[0]
				params['preset']=dbinfo[1]
				params["dbimages"]=True
				params["continue"]=True # continue should be on for dbimages option
			else:
				apDisplay.printError("dbimages must include both \'session\' and \'preset\'"+\
					"parameters (ex: \'07feb13a,en\')\n")
		elif (elements[0]=='alldbimages'):
			params['session']=elements[1]
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
			apDisplay.printError("undefined parameter \'"+arg+"\'\n")
	"""

def runFindEM(params,file):
	apDisplay.printError("this FindEM function no longer exists here")

def getProjectId(params):
	projectdata=project.ProjectData()
	projects=projectdata.getProjectExperiments()
	for i in projects.getall():
		if i['name']==params['session']:
			params['projectId']=i['projectId']
	if not params['projectId']:
		apDisplay.printError("no project associated with this session\n")
	return
	
def getOutDirs(params):
	sessionq=data.SessionData(name=params['session']['name'])
	sessiondata=db.query(sessionq)
	impath=sessiondata[0]['image path']
	params['imgdir']=impath+'/'

	if params['outdir']:
		pass
	else:
		outdir=os.path.split(impath)[0]
		outdir=os.path.join(outdir,'selexon/')
		params['outdir']=outdir

	params['rundir']=os.path.join(params['outdir'],params['runid'])
	
	if os.path.exists(params['rundir']):
		print " !!! WARNING: run directory for \'"+str(params['runid'])+"\' already exists.\n"
		if params["continue"]==False:
			print " !!! WARNING: continue option is OFF if you WILL overwrite previous run."
			time.sleep(10)
	else:
		os.makedirs(params['rundir'],0777)

	return(params)

def createImageLinks(imagelist):
	apDisplay.printError("this ViewIt function no longer exists here")

def findPeaks(params,file):
	apDisplay.printError("this ViewIt function no longer exists here")

def createJPG(params,img):
	apDisplay.printError("this ViewIt function no longer exists here")

def findCrud(params,file):
	apDisplay.printError("this ViewIt function no longer exists here")

def getImgSize(imgname):
	apDisplay.printWarning("this apDatabase function getImagesFromDB no longer exists here")
	return apDatabase.getImgSizeFromName(imgname)

def checkTemplates(params,upload=None):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	return apTemplate.checkTemplates(params, upload=upload)

def dwnsizeImg(params, imgdict):
	apDisplay.printWarning("this apFindEM function no longer exists here")
	apFindEM.processAndSaveImage(imgdict, params)
	return

def dwnsizeTemplate(params,filename):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.dwnsizeTemplate(filename, params)
	return

def binImg(img,binning):
	apDisplay.printWarning("this apImage function no longer exists here")
	return apImage.binImg(img,binning)

def filterImg(img,apix,res):
	apDisplay.printWarning("this apImage function no longer exists here")
	return apImage.filterImg(img,apix,res)

def pik2Box(params,file):
	apDisplay.printWarning("this apParticle function pik2Box no longer exists here")
	return apParticle.pik2Box(params,file)

def writeSelexLog(commandline, file=".selexonlog"):
	apDisplay.printError("this apParam function no longer exists here")

def getDoneDict(selexondonename):
	apDisplay.printError("this apLoop function no longer exists here")

def writeDoneDict(donedict,selexondonename):
	apDisplay.printError("this apLoop function no longer exists here")

def doneCheck(donedict,im):
	apDisplay.printError("this apLoop function no longer exists here")

def getImageData(imgname):
	apDisplay.printWarning("this apDatabase function getImageData no longer exists here")
	return apDatabase.getImageData(imgname)

def getPixelSize(imgdict):
	apDisplay.printWarning("this apDatabase function getPixelSize no longer exists here")
	return apDatabase.getPixelSize(imgdict)

def getImagesFromDB(session, preset):
	apDisplay.printWarning("this apDatabase function getImagesFromDB no longer exists here")
	return apDatabase.getImagesFromDB(session, preset)

def getAllImagesFromDB(session):
	apDisplay.printWarning("this apDatabase function getAllImagesFromDB no longer exists here")
	return apDatabase.getAllImagesFromDB(session)

def getDBTemplates(params):
	apDisplay.printWarning("this apDatabase function getDBTemplates no longer exists here")
	apDatabase.getDBTemplates(params)

def rescaleTemplates(img,params):
	#why is img passed? It is not used.
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.rescaleTemplates(params)
	return
	
def scaleandclip(fname,scalefactor,newfname):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.scaleAndClipTemplate(fname,scalefactor,newfname)
	return

def getDefocusPair(imagedata):
	apDisplay.printError("this DefocusPair function no longer exists here")

def getShift(imagedata1,imagedata2):
	apDisplay.printError("this DefocusPair function no longer exists here")

def findSubpixelPeak(image, npix=5, guess=None, limit=None, lpf=None):
	apDisplay.printError("this DefocusPair function no longer exists here")

def recordShift(params,img,sibling,peak):
	apDisplay.printError("this DefocusPair function no longer exists here")

def insertShift(img,sibling,peak):
	apDisplay.printError("this DefocusPair function no longer exists here")

def insertManualParams(params,expid):
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=partdb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into run.dbparticledata
 	# then create a new selexonParam entry
 	if not(runids):
		print "inserting manual runId into database"
 		manparams=appionData.ApSelectionParamsData()
 		manparams['ApSelectionRunData']=runq
 		manparams['diam']=params['diam']
 		partdb.insert(runq)
 	       	partdb.insert(manparams)

def insertSelexonParams(params,expid):

	### query for identical params ###
	selexonparamsq=appionData.ApSelectionParamsData()
 	selexonparamsq['diam']=params['diam']
 	selexonparamsq['bin']=params['bin']
 	selexonparamsq['manual_thresh']=params['thresh']
 	selexonparamsq['auto_thresh']=params['autopik']
 	selexonparamsq['lp_filt']=params['lp']
 	selexonparamsq['hp_filt']=params['hp']
 	#selexonparamsq['crud_diameter']=params['cdiam']
 	#selexonparamsq['crud_blur']=params['cblur']
 	#selexonparamsq['crud_low']=params['clo']
 	#selexonparamsq['crud_high']=params['chi']
 	#selexonparamsq['crud_std']=params['cstd']
	selexonparamsdata=partdb.query(selexonparamsq, results=1)
	
	### query for identical run name ###
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=partdb.query(runq, results=1)
	
 	# if no run entry exists, insert new run entry into dbappiondata
 	if not(runids):
		runq['params']=selexonparamsq
		if not selexonparamsdata:
			partdb.insert(selexonparamsq)
		partdb.insert(runq)
		#insert template params
 		for n in range(0,len(params['templateIds'])):
			insertTemplateRun(params,runq,n)
	
	# if continuing a previous run, make sure that all the current
 	# parameters are the same as the previous
 	else:
		if runids[0]['params']!=selexonparamsdata[0]:
			apDisplay.printError("All parameters for a single selexon run must be identical! \n"+\
					     "please check your parameter settings.")
		_checkTemplateParams(params,runq)

	return

def _checkTemplateParams(params,runq):
	templaterunq=appionData.ApTemplateRunData(selectionrun=runq)
	templaterundata=partdb.query(templaterunq)
	#make sure of using same number of templates
	if len(params['templateIds'])!=len(templaterundata):
		apDisplay.printError("All parameters for a selexon run must be identical!"+\
			"You do not have the same number of templates as your last run")
	# check all templates
		
	
	if params['multiple_range']:
		for n in range(0,len(params['templateIds'])):
			strt=params["startang"+str(n+1)]
			end=params["endang"+str(n+1)]
			incr=params["incrang"+str(n+1)]
			tmpltimagedata=partdb.direct_query(data.ApTemplateImageData,params['templateIds'][n])
			tmpltrunq=appionData.ApTemplateRunData()
			tmpltrunq['selectionrun']=runq
			tmpltrunq['template']=tmpltimagedata
			tmpltrundata=partdb.query(tmpltrunq,results=1)
			if (tmpltrundata[0]['range_start']!=strt or
				tmpltrundata[0]['range_end']!=end or
				tmpltrundata[0]['range_incr']!=incr):
				apDisplay.printError("All parameters for a selexon run must be identical!"+\
					"Template search ranges are not the same as your last run")
	else:
		if (templaterundata[0]['range_start']!=params['startang'] or
			templaterundata[0]['range_end']!=params['endang'] or
			templaterundata[0]['range_incr']!=params['incrang']):
			apDisplay.printError("All parameters for a selexon run must be identical!"+\
				"Template search ranges are not the same as your last run")
	return
			

"""	
def insertSelexonParams(params,expid):

	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=partdb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into run.dbparticledata
 	# then create a new selexonParam entry
 	if not(runids):
		if len(params['templatelist'])==1:
			if params['templateIds']:
				imgname=params['templateIds'][0]
			else:
				imgname=params['abspath']+params['template']+'.mrc'
			insertTemplateRun(params,runq,imgname,params['startang'],params['endang'],params['incrang'])
		else:
			for i in range(1,len(params['templatelist'])+1):
				if params['templateIds']:
					imgname=params['templateIds'][i-1]
				else:
					imgname=params['abspath']+params['template']+str(i)+'.mrc'
				if (params["multiple_range"]==True):
					strt=params["startang"+str(i)]
					end=params["endang"+str(i)]
					incr=params["incrang"+str(i)]
					insertTemplateRun(params,runq,imgname,strt,end,incr)
				else:
					insertTemplateRun(params,runq,imgname,params['startang'],params['endang'],params['incrang'])
 		selexonparams=appionData.ApSelectionParamsData()
 		selexonparams['run']=runq
 		selexonparams['diam']=params['diam']
 		selexonparams['bin']=params['bin']
 		selexonparams['manual_thresh']=params['thresh']
 		selexonparams['auto_thresh']=params['autopik']
 		selexonparams['lp_filt']=params['lp']
 		selexonparams['hp_filt']=params['hp']
 		selexonparams['crud_diameter']=params['cdiam']
 		selexonparams['crud_blur']=params['cblur']
 		selexonparams['crud_low']=params['clo']
 		selexonparams['crud_high']=params['chi']
 		selexonparams['crud_std']=params['cstd']
 		partdb.insert(runq)
 	       	partdb.insert(selexonparams)
		
 	# if continuing a previous run, make sure that all the current
 	# parameters are the same as the previous
 	else:
		# get existing selexon parameters from previous run
 		partq=appionData.ApSelectionParamsData(run=runq)
		tmpltq=appionData.ApTemplateRunData(run=runq)

 		partresults=partdb.query(partq, results=1)
		tmpltresults=partdb.query(tmpltq)
		selexonparams=partresults[0]
		# make sure that using same number of templates
		if len(params['templatelist'])!=len(tmpltresults):
			apDisplay.printError("All parameters for a selexon run must be identical!"+\
				"You do not have the same number of templates as your last run")
		# param check if using multiple ranges for templates
		if (params['multiple_range']==True):
			# check that all ranges have same values as previous run
			for i in range(0,len(params['templatelist'])):
				if params['templateIds']:
					tmpltimgq=partdb.direct_query(data.ApTemplateImageData,params['templateIds'][i])
				else:
					tmpltimgq=appionData.ApTemplateImageData()
					tmpltimgq['templatepath']=params['abspath']
					tmpltimgq['templatename']=params['template']+str(i+1)+'.mrc'

				tmpltrunq=appionData.ApTemplateRunData()

				tmpltrunq['run']=runq
				tmpltrunq['template']=tmpltimgq

				tmpltNameResult=partdb.query(tmpltrunq,results=1)
				strt=params["startang"+str(i+1)]
				end=params["endang"+str(i+1)]
				incr=params["incrang"+str(i+1)]
				if (tmpltNameResult[0]['range_start']!=strt or
				    tmpltNameResult[0]['range_end']!=end or
				    tmpltNameResult[0]['range_incr']!=incr):
					apDisplay.printError("All parameters for a selexon run must be identical!"+\
						"Template search ranges are not the same as your last run")
		# param check for single range
		else:
			if (tmpltresults[0]['range_start']!=params["startang"] or
			    tmpltresults[0]['range_end']!=params["endang"] or
			    tmpltresults[0]['range_incr']!=params["incrang"]):
				apDisplay.printError("All parameters for a selexon run must be identical!"+\
					"Template search ranges are not the same as your last run")
 		if (selexonparams['diam']!=params['diam'] or
		    selexonparams['bin']!=params['bin'] or
		    selexonparams['manual_thresh']!=params['thresh'] or
		    selexonparams['auto_thresh']!=params['autopik'] or
		    selexonparams['lp_filt']!=params['lp'] or
		    selexonparams['hp_filt']!=params['hp'] or
		    selexonparams['crud_diameter']!=params['cdiam'] or
		    selexonparams['crud_blur']!=params['cblur'] or
		    selexonparams['crud_low']!=params['clo'] or
		    selexonparams['crud_high']!=params['chi'] or
		    selexonparams['crud_std']!=params['cstd']):
			apDisplay.printError("All parameters for a selexon run must be identical!"+\
				"please check your parameter settings.")
	return
"""


def insertTemplateRun(params,runq,templatenum):

	tid=params['templateIds'][templatenum]
	templateimagedata=partdb.direct_query(data.ApTemplateImageData,tid)
	# if no templates in the database, exit
	if not (templateimagedata):
		apDisplay.printError("Template '"+tid+"' not found in database. Use uploadTemplates.py")

	if params['multiple_range']:
		strt=params["startang"+str(templatenum+1)]
		end=params["endang"+str(templatenum+1)]
		incr=params["incrang"+str(templatenum+1)]
	else:
		strt=params['startang']
		end=params['endang']
		incr=params['incrang']
	
	templaterunq=appionData.ApTemplateRunData()
	templaterunq['selectionrun']=runq	
	templaterunq['template']=templateimagedata
	templaterunq['range_start']=float(strt)
	templaterunq['range_end']=float(end)
	templaterunq['range_incr']=float(incr)
	partdb.insert(templaterunq)
	return

def insertTemplateImage(params):
	for name in params['templatelist']:
		templateq=appionData.ApTemplateImageData()
		templateq['templatepath']=params['abspath']
		templateq['templatename']=name
		templateId=partdb.query(templateq, results=1)
	        #insert template to database if doesn't exist
		if not (templateId):
			print "Inserting",name,"into the template database"
			templateq['apix']=params['apix']
			templateq['diam']=params['diam']
			templateq['description']=params['description']
			templateq['project|projects|project']=params['projectId']
			partdb.insert(templateq)
		else:
			print "Warning: template already in database."
			print "Not reinserting"
	return

def insertParticlePicks(params,imgdict,expid,manual=False):
	apDisplay.printWarning("this apParticle function insertParticlePicks no longer exists here")
	apParticle.insertParticlePicks(params,imgdict,expid,manual)
