#!/usr/bin/python -O
# Will create a stack file based on a set of input parameters using EMAN's batchboxer

#pythonlib
import os
import re
import sys 
import math
import string
import time
#sinedon
try:
	import sinedon.data as data
except:
	import data
#leginon
try:
	import leginondata
except:
	import data as leginondata
#appion
import appionData
import apDisplay
import apParticle
import apParam
import apDB
import apDatabase
import apCtf
import apMask
import apXml
import apImage
import apDefocalPairs
import apEMAN
try:
	import apMatlab
except:
	pass

db   = apDB.db
apdb = apDB.apdb

def printHelp():
	print "\nUsage:\nmakestack.py <boxfile> [single=<stackfile>] [outdir=<path>] [ace=<n>] [boxsize=<n>] [inspected or inspectfile=<file>] [bin=<n>] [phaseflip] [noinvert] [spider] mindefocus=<n> maxdefocus=<n> [partlimit=<n>] [defocpair=<preset>] [lp=<n>] [hp=<n>]\n"
	print "Examples:\nmakestack.py extract/001ma.box single=stacks/start.hed ace=0.8 boxsize=180 inspected"
	print "makestack.py extract/*.box outdir=stacks/noctf/ ace=0.8 boxsize=180\n"
	print "* Supports wildcards - By default a stack file of the same name as the box file"
	print "  will be created in the current directory *\n"
	appiondir = apParam.getAppionDirectory()
	funcxml = os.path.join(appiondir,"xml","makestack.xml")
	xmldict = apXml.readOneXmlFile(funcxml)
	apXml.printHelp(xmldict)
	sys.exit(1)

def createDefaults():
	# create default values for parameters
	params={}
	params['imgs']=[]
	params['runid']=None
	params['single']=None
	params['aceCutoff']=None
	params['boxSize']=None
	params['checkImage']=None
	params['inspectfile']=None
	params['phaseFlipped']=False
	params['apix']=0
	params['kv']=0
	params['tiltangle']=None
	params['inverted']=True
	params['spider']=False
	params['df']=0.0
	params['minDefocus']=None
	params['maxDefocus']=None
	params['description']=None
	params['selexonId']=None
	params['sessionname']=None
	params['medium']=None
	params['normalized']=True
	params['correlationMin']=None
	params['correlationMax']=None
	params['checkMask']=None
	params['commit']=False
	params['outdir']=os.path.abspath(".")
	params['particleNumber']=0
	params['bin']=1
	params['partlimit']=None
	params['defocpair']=False
	params['uncorrected']=False
	params['stig']=False
	params['matlab']=None
	params['fileType']='imagic'
	params['lowpass']=None
	params['highpass']=None
	return params

def parseInput(args):
	# check that there are enough input parameters
	if (len(args)<2 or args[1] == 'help') :
		printHelp()

	lastarg=1

	# first get all images
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		elif (arg=='phaseflip' or arg=='commit' or 'invert' in arg or arg=='spider'):
			break
		else:
			boxfile=arg
			if (os.path.exists(boxfile)):
				mrcfileroot.append(os.path.splitext(boxfile)[0])
			else:
				print ("file '%s' does not exist \n" % boxfile)
				sys.exit()
		lastarg+=1
	params['imgs']=mrcfileroot

	# next get all selection parameters
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='outdir'):
			params['outdir'] = os.path.abspath(elements[1])
		elif (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='single'):
			params['single']=elements[1]
		elif (elements[0]=='ace'):
			params['aceCutoff']=float(elements[1])
		elif (elements[0]=='selexonmin'):
			params['correlationMin']=float(elements[1])
		elif (elements[0]=='selexonmax'):
			params['correlationMax']=float(elements[1])
		elif (elements[0]=='tiltangle'):
			params['tiltangle']=abs(float(elements[1]))
		elif (elements[0]=='maskassess'):
			params['checkMask']=elements[1]
		elif (elements[0]=='boxsize'):
			params['boxSize']=int(elements[1])
		elif (elements[0]=='inspectfile'):
			params['inspectfile']=elements[1]
		elif (elements[0]=='medium'):
			params['medium']=elements[1]
		elif (elements[0]=='bin'):
			params['bin']=int(elements[1])
		elif (elements[0]=='sessionname'):
			params['sessionname']=elements[1]
		elif (elements[0]=='lp'):
			params['lowpass']=float(elements[1])
		elif (elements[0]=='hp'):
			params['highpass']=float(elements[1])
		elif (arg=='inspected'):
			params['checkImage']=True
		elif (arg=='nonorm'):
			params['normalized']=False
		elif (arg=='phaseflip'):
			params['phaseFlipped']=True
		elif (arg=='noinvert'):
			params['inverted']=False
		elif (arg=='invert'):
			params['inverted']=True
		elif (arg=='spider'):
			params['spider']=True
			params['fileType']='spider'
		elif (arg=='commit'):
			params['commit']=True
			# if commit is set, must have a runid:
			if not params['runid']:
				params['runid']='stack1'
		elif (elements[0]=='mindefocus'):
			mindf=float(elements[1])
			if mindf > 0:
				print "mindefocus must be negative and specified in meters"
				sys.exit(1)
			else:
				params['minDefocus']=mindf*1e6
		elif (elements[0]=='maxdefocus'):
			maxdf=float(elements[1])
			if maxdf > 0:
				print "maxdefocus must be negative and specified in meters" 
				sys.exit(1)
			else:
				params['maxDefocus']=maxdf*1e6
		elif (elements[0]=='description'):
			params['description']=elements[1]
		elif (elements[0]=='prtlrunId'):
			params['selexonId']=int(elements[1])
		elif elements[0]=='partlimit':
			params['partlimit']=int(elements[1])
		elif arg=='defocpair':
			params['defocpair']=True
		elif arg=='uncorrected':
			params['uncorrected']=True
		elif arg=='stig':
			params['stig']=True
			params['phaseFlipped']=False	
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)
	return params

def checkParamConflicts(params):
	if params['medium'] != "carbon" and params['medium'] != "ice" and params['medium'] != None:
		apDisplay.printError("medium must be either 'carbon' or 'ice'")
	# if saving to the database, stack must be a single file
	if params['commit'] and not params['single']:
		apDisplay.printError("When committing to database, stack must be a single file.\n"+\
			"use the 'single=<filename>' option")
	# if getting particles from db or committing, a box size must be set
	if (params['commit'] or params['selexonId']) and not params['boxSize']:
		apDisplay.printError("Specify a box size")
	return

def getFilePath(imgdict):
	session=imgdict.split('_')[0] # get session from beginning of file name
	f=os.popen('dbemgetpath %s' % session)
	result=f.readlines()
	f.close()
	if (result==[]):
		print "rawdata directory does not exist!\n"
		sys.exit(1)
	else:
		words=result[0].split('\t')
		path=string.rstrip(words[1])
	return path

def checkInspectFile(imgdict):
	filename=imgdict['filename']+'.mrc'
	f=open(params['inspectfile'],'r')
	results=f.readlines()
	status=''
	for line in results:
		words=line.split('\t')
		if (string.find(words[0],filename)==0):
			status=words[1]
			status.rstrip('\n')
			break
	if (status.rstrip('\n')=='keep'):
		return (True)
	return (False)


def checkInspectDB(imgdata):
	status = apDatabase.getImageStatus(imgdata)
	if status is False:
		return False
	keep = apDatabase.getImgAssessmentStatus(imgdata)
	return keep

def checkPairInspectDB(imgdata,params):
	aq=appionData.ApAssessmentData()
	#sibimagedata = db.direct_query(leginondata.AcquisitionImageData,params['sibpairs'][imgdata.dbid])
	sibimagedata = apDefocalPairs.getDefocusPair(imgdata)
	aq['image']=sibimagedata
	adata=apdb.query(aq)	


	keep=None
	if adata:
		#check results of only most recent run
		if adata[0]['selectionkeep']==True:
			keep=True
		else:
			keep=False
	return(keep)

def batchBox(params, imgdict):
	imgname = imgdict['filename']
	shortname = apDisplay.short(imgname)
	print "processing:",apDisplay.short(imgname)
	if params['uncorrected']:
		tmpname='temporaryCorrectedImage.mrc'
		imgarray = apImage.correctImage(imgdict, params)
		imgpath = os.path.join(params['outdir'],tmpname)
		apImage.arrayToMrc(imgarray,imgpath)
		print "processing", imgpath		
	elif params['stig']:
		apMatlab.runAceCorrect(imgdict,params)	
		tmpname = imgdict['filename']
		imgpath = os.path.join(params['outdir'],tmpname)
	else:
		imgpath = os.path.join(params['filepath'], imgname+".mrc")
	output = os.path.join(params['outdir'], imgname+".hed")

	# if getting particles from database, a temporary
	# box file will be created
	if params['selexonId']:
		dbbox=os.path.join(params['outdir'], "temporaryParticlesFromDB.box")
		if params['defocpair']:
			particles,shift = apParticle.getDefocPairParticles(imgdict,params)
		else:
			particles = apParticle.getParticles(imgdict, params['selexonId'])
			shift = {'shiftx':0, 'shifty':0,'scale':1}
		if len(particles) > 0:			
			###apply limits
			if params['correlationMin'] or params['correlationMax']:
				particles=eliminateMinMaxCCParticles(particles,params)
			
			###apply masks
			if params['checkMask']:
				particles = eliminateMaskedParticles(particles,params,imgdict)
			
			###save particles
			if len(particles) > 0:
				hasparticles=True
				saveParticles(particles,shift,dbbox,params,imgdict)
			else:
				hasparticles=False
				apDisplay.printColor(shortname+".mrc had no unmasked particles and has been rejected\n","cyan")
		else:
			hasparticles=False
			apDisplay.printColor(shortname+".mrc had no particles and has been rejected\n","cyan")
	else:
		dbbox=imgname+".box"
		hasparticles=True
	
	if hasparticles:
		#count number of particles in box file
		f=open(dbbox,'r')
		lines=f.readlines()
		f.close()
		nptcls=len(lines)
		# write batchboxer command
		if params['selexonId']:
			cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i" %(imgpath, dbbox, output, params['boxSize'])
		elif params['boxSize']:
			cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i insideonly" %(imgpath, dbbox, output, params['boxSize'])
		else: 
	 		cmd="batchboxer input=%s dbbox=%s output=%s insideonly" %(imgpath, dbbox, output)
	
		apDisplay.printMsg("boxing "+str(nptcls)+" particles")
		apEMAN.executeEmanCmd(cmd)
		#f=os.popen(cmd)
		#f.close()
		if params['stig']:
			os.remove(os.path.join(params['outdir'],tmpname))
		return(nptcls)
	else:
		if params['stig']:
			os.remove(os.path.join(params['outdir'],tmpname))
		return(0)
		

	
def eliminateMaskedParticles(particles,params,imgdata):
	newparticles = []
	eliminated = 0
	sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
	if params['defocpair']:
		imgdata = apDefocalPairs.getTransformedDefocPair(imgdata,2)
#		print imgdata.dbid
	maskimg,maskbin = apMask.makeInspectedMask(sessiondata,params['checkMask'],imgdata)
	if maskimg is not None:
		for prtl in particles:
			binnedcoord = (int(prtl['ycoord']/maskbin),int(prtl['xcoord']/maskbin))
			if maskimg[binnedcoord] != 0:
				eliminated += 1
			else:
				newparticles.append(prtl)
		print eliminated,"particle(s) eliminated due to masking"
	else:
		print "no masking"
		newparticles = particles
	return newparticles

def eliminateMinMaxCCParticles(particles,params):
	newparticles = []
	eliminated = 0
	for prtl in particles:
		if params['correlationMin'] and prtl['correlation'] < params['correlationMin']:
			eliminated += 1
		elif params['correlationMax'] and prtl['correlation'] > params['correlationMax']:
			eliminated += 1
		else:
			newparticles.append(prtl)
	if eliminated > 0:
		apDisplay.printMsg(str(eliminated)+" particle(s) eliminated due to min or max correlation cutoff")
	return newparticles

def eliminateMsgPNoKeepParticles(particles,params):
	newparticles = []
	eliminated = 0
	keepmin = 1
	#### Very slow this way ####
	for prtl in particles:
		if apParticle.getMsgPKeepStatus(p,refinetree,1) >=keepmin:
			newparticles.append(prtl)
		else:
			eliminated += 1
	if eliminated > 0:
		apDisplay.printMsg(str(eliminated)+" particle(s) eliminated due to min or max correlation cutoff")
	return newparticles

def saveParticles(particles,shift,dbbox,params,imgdict):
	imgname = imgdict['filename']
	plist=[]
	box=params['boxSize']
	imgxy=imgdict['camera']['dimension']
	eliminated=0
	for i,prtl in enumerate(particles):
		xcoord=int(math.floor(shift['scale']*(prtl['xcoord']-shift['shiftx'])-(box/2)+0.5))
		ycoord=int(math.floor(shift['scale']*(prtl['ycoord']-shift['shifty'])-(box/2)+0.5))

		if (xcoord>0 and xcoord+box <= imgxy['x'] and ycoord>0 and ycoord+box <= imgxy['y']):
			plist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
			# save the particles to the database
			if params['commit']:
				stackpq=appionData.ApStackParticlesData()
				stackpq['stack']=params['stackId']
				stackpq['stackRun']=params['stackRun']
				stackpq['particle']=prtl
				params['particleNumber'] += 1
				stackpq['particleNumber']=params['particleNumber']
				apdb.insert(stackpq)
		else:
			eliminated+=1
	if eliminated > 0:
		apDisplay.printMsg(str(eliminated)+" particle(s) eliminated because out of bounds")
	#write boxfile
	boxfile=open(dbbox,'w')
	boxfile.writelines(plist)
	boxfile.close()
	
def phaseFlip(imgdata, params):
	imgname = imgdata['filename']
	infile  = os.path.join(params['outdir'], imgname+".hed")
	outfile = os.path.join(params['outdir'], imgname+".ctf.hed")
	voltage = (imgdata['scope']['high tension'])/1000
	defocus = 1.0e6 * apCtf.getBestDefocusForImage(imgdata)

	if defocus > 0:
		apDisplay.printError("defocus is positive "+str(defocus)+" for image "+shortname)
	elif defocus < -1.0e3:
		apDisplay.printError("defocus is very big "+str(defocus)+" for image "+shortname)
	elif defocus > -1.0e-3:
		apDisplay.printError("defocus is very small "+str(defocus)+" for image "+shortname)

	cmd="applyctf %s %s parm=%f,200,1,0.1,0,17.4,9,1.53,%i,2,%f setparm flipphase" % ( infile,\
	  outfile, defocus, voltage, params['apix'])
	apDisplay.printMsg("phaseflipping particles with defocus "+str(round(defocus,3))+" microns")

	f=os.popen(cmd)
	f.close()

def singleStack(params,imgdict):
	imgname = imgdict['filename']
 	if params['phaseFlipped'] is True:
		imgpath = os.path.join(params['outdir'], imgname+'.ctf.hed')
	else:
		imgpath = os.path.join(params['outdir'], imgname+'.hed')
	output = os.path.join(params['outdir'], params['single'])

	cmd="proc2d %s %s" %(imgpath, output)
	if params['normalized'] is True:
		cmd += " norm=0.0,1.0"

	if params['highpass'] or params['lowpass']:
		cmd += " apix=%s" % params['apix']
		if params['highpass']:
			cmd += " hp=%s" % params['highpass']
		if params['lowpass']:
			cmd += " lp=%s" % params['lowpass']
			
	# bin images if specified
	if params['bin'] != 1:
		cmd += " shrink="+str(params['bin'])
		
	# unless specified, invert the images
	if params['inverted'] is True:
		cmd += " invert"

	# if specified, create spider stack
	if params['spider'] is True:
		cmd += " spiderswap"

 	apDisplay.printMsg("appending particles to stack: "+output)
	# run proc2d & get number of particles
	f=os.popen(cmd)
 	lines=f.readlines()
	f.close()
	for n in lines:
		words=n.split()
		if 'images' in words:
			count=int(words[-2])

	# create particle log file
	partlogfile = os.path.join(params['outdir'], ".particlelog")
	f = open(partlogfile, 'a')
	for n in range(count-params['particle']):
		particlenum=str(1+n+params['particle'])
		line = str(particlenum)+'\t'+os.path.join(params['filepath'], imgname+".mrc")
		f.write(line+"\n")
	f.close()
	params['particle'] = count
	
	os.remove(os.path.join(params['outdir'], imgname+".hed"))
	os.remove(os.path.join(params['outdir'], imgname+".img"))
	if params['phaseFlipped'] is True:
		os.remove(os.path.join(params['outdir'], imgname+".ctf.hed"))
		os.remove(os.path.join(params['outdir'], imgname+".ctf.img"))

# since we're using a batchboxer approach, we must first get a list of
# images that contain particles
def getImgsFromSelexonId(params):
	startt = time.time()
	apDisplay.printMsg("Finding images that have particles for selection run: id="+str(params['selexonId']))

	# get selection run id
	selexonrun = apdb.direct_query(appionData.ApSelectionRunData, params['selexonId'])
	if not (selexonrun):
		apDisplay.printError("specified runId '"+str(params['selexonId'])+"' is not in database")
	
	# from id get the session
	params['sessionid'] = selexonrun['session']

	# get all images from session
	apDisplay.printMsg("Getting images")
	dbimgq = leginondata.AcquisitionImageData(session=params['sessionid'])
	allimgtree = db.query(dbimgq, readimages=False)

	if not (allimgtree):
		apDisplay.printError("no images associated with this runId")

	# for every image, find corresponding image entry in the particle database
	apDisplay.printMsg("Finding corresponding image entry in the particle database")
	partimgtree=[]

	for imgdata in allimgtree:
		pimgq = appionData.ApParticleData()
		pimgq['image'] = imgdata
		pimgq['selectionrun'] = selexonrun
		pimg = apdb.query(pimgq, results=1)
		if pimg:
			partimgtree.append(imgdata)
	apDisplay.printMsg("completed in "+apDisplay.timeString(time.time()-startt))

	totalimgs = str(len(allimgtree))
	partimgs = str(len(partimgtree))
	apDisplay.printMsg("selected "+partimgs+" of all "+totalimgs+" images that have particles")

	return (partimgtree)

def getImgsDefocPairFromSelexonId(params):
	startt = time.time()
	apDisplay.printMsg("Finding defoc pair images that have particles for selection run: id="+str(params['selexonId']))

	# get selection run id
	selexonrun=apdb.direct_query(appionData.ApSelectionRunData,params['selexonId'])
	if not (selexonrun):
		apDisplay.printError("specified runId '"+str(params['selexonId'])+"' not in database")
	
	# from id get the session
	params['sessionid']=selexonrun['session']

	# get all images from session
	dbimgq=leginondata.AcquisitionImageData(session=params['sessionid'])
	dbimginfo=db.query(dbimgq,readimages=False)

	if not (dbimginfo):
		apDisplay.printError("no images associated with this runId")

	apDisplay.printMsg("Find corresponding image entry in the particle database")
	# for every image, find corresponding image entry in the particle database
	dbimglist=[]
	params['sibpairs']={}
	for imgdata in dbimginfo:
		pimgq=appionData.ApParticleData()
		pimgq['image']=imgdata
		pimgq['selectionrun']=selexonrun
		pimg=apdb.query(pimgq, results=1)
		if pimg:
			siblingimage = apDefocalPairs.getTransformedDefocPair(imgdata,1)
			if siblingimage:
				#create a dictionary for keeping the dbids of image pairs so we don't have to query later
				params['sibpairs'][siblingimage.dbid] = imgdata.dbid
				dbimglist.append(siblingimage)
			else:
				apDisplay.printWarning("no shift data for "+apDisplay.short(imgdata['filename']))
	apDisplay.printMsg("completed in "+apDisplay.timeString(time.time()-startt))
	return (dbimglist)

def insertStackRun(params):
	stparamq=appionData.ApStackParamsData()
	paramlist = ('boxSize','bin','phaseFlipped','aceCutoff','correlationMin','correlationMax',
		'checkMask','checkImage','minDefocus','maxDefocus','fileType','inverted','normalized', 'defocpair','lowpass','highpass')

	for p in paramlist:
		if p in params:
			stparamq[p] = params[p]
	paramslist=apdb.query(stparamq)

	# make sure that NULL values were not filled in during query
	goodplist=None
	for plist in paramslist:
		notgood=None
		for p in paramlist:
			if plist[p] != params[p]:
				notgood=True
		if notgood is None:
			goodplist=plist
			continue

	# create a stack object
	stackq = appionData.ApStackData()
	stackq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
	stackq['name'] = params['single']

	# create a stackRun object
	runq = appionData.ApStackRunData()
	runq['stackRunName'] = params['runid']
	runq['session'] = params['sessionid']

        # see if stack already exists in the database (just checking path)
	stacks = apdb.query(stackq, results=1)

	# recreate stack object
	stackq = appionData.ApStackData()
	stackq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
	stackq['name'] = params['single']
	stackq['description'] = params['description']
	
	params['stackId']=stackq

	runids = apdb.query(runq, results=1)
	# recreate a stackRun object
	runq = appionData.ApStackRunData()
	runq['stackRunName'] = params['runid']
	runq['session'] = params['sessionid']
	if goodplist:
		runq['stackParams'] = goodplist
	else:
		runq['stackParams'] = stparamq

	params['stackRun']=runq

	# create runinstack object
	rinstackq = appionData.ApRunsInStackData()

	rinstackq['stackRun']=params['stackRun']
	rinstackq['stack']=params['stackId']

	# if not in the database, make sure run doesn't already exist
	if not stacks:
		if not runids:
			print "Inserting stack parameters into DB"
			apdb.insert(rinstackq)
		else:
			apDisplay.printError("Run name '"+params['runid']+"' already in the database")
	
	# if it's in the database, make sure that all other
	# parameters are the same, since stack will be re-written
	else:
		# make sure description is the same:
		if stacks[0]['description']!=params['description']:
			apDisplay.printError("Stack description is not the same!")
		# make sure the the run is the same:
		rinstack = apdb.query(rinstackq, results=1)
		
		## if no runinstack found, find out which parameters are wrong:
		if not rinstack:
			rinstackq = appionData.ApRunsInStackData()
			rinstackq['stack'] = apdb.query(params['stackId'])[0]
			correct_rinstack=apdb.query(rinstackq)
			for i in correct_rinstack[0]['stackRun']['stackParams']:
				if correct_rinstack[0]['stackRun']['stackParams'][i] != stparamq[i]:
					apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
			apDisplay.printError("All parameters for a particular stack must be identical! \n"+\
						     "please check your parameter settings.")
		apDisplay.printWarning("Recreating an existing stack! Previous stack will be overwritten!")

def rejectImage(imgdata, params):
	shortname = apDisplay.short(imgdata['filename'])

	### check if the image has inspected, in file or in database
	if params['inspectfile'] and checkInspectFile(imgdata) is False:
		apDisplay.printColor(shortname+".mrc has been rejected in inspection file\n","cyan")
		return False

	if params['checkImage']:
		if checkInspectDB(imgdata) is False:
			apDisplay.printColor(shortname+".mrc has been rejected by manual inspection\n","cyan")
			return False
		if params['defocpair'] and checkPairInspectDB(imgdata, params) is False:
			apDisplay.printColor(shortname+".mrc has been rejected by manual defocpair inspection\n","cyan")
			return False

	if params['tiltangle'] is not None:
		tiltangle = abs(apDatabase.getTiltAngleDeg(imgdata))
		if abs(params['tiltangle'] - tiltangle) > 2.0:
			apDisplay.printColor(shortname+".mrc has been rejected tiltangle: "+str(round(tiltangle,1))+\
				" != "+str(round(params['tiltangle'],1))+"\n","cyan")
			return False

	### Get CTF values
	ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)
	
 	if ctfvalue is None:
		if params['aceCutoff'] or params['minDefocus'] or params['maxDefocus'] or params['phaseFlipped']:
			apDisplay.printColor(shortname+".mrc was rejected because it has no ACE values\n","cyan")
			return False
		else:
			apDisplay.printWarning(shortname+".mrc has no ACE values")

 	if ctfvalue is not None:
		apCtf.ctfValuesToParams(ctfvalue, params)

		### check that ACE estimation is above confidence threshold
		if params['aceCutoff'] and conf < params['aceCutoff']:
				apDisplay.printColor(shortname+".mrc is below ACE threshold (conf="+str(round(conf,3))+")\n","cyan")
				return False

		### skip micrograph that have defocus above or below min & max defocus levels
		if params['minDefocus'] and params['df'] > params['minDefocus']:
			apDisplay.printColor(shortname+".mrc defocus ("+str(round(params['df'],3))+\
				") is less than mindefocus ("+str(params['minDefocus'])+")\n","cyan")
			return False
		if params['maxDefocus'] and params['df'] < params['maxDefocus']:
			apDisplay.printColor(shortname+".mrc defocus ("+str(round(params['df'],3))+\
				") is greater than maxdefocus ("+str(params['maxDefocus'])+")\n","cyan")
			return False

	return True

def getStackId(params):
	# create a stackRun object
	stackq = appionData.ApStackData()
	stackq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
	stackq['name'] = params['single']

	try:
		stackdata = apdb.query(stackq, results=1)[0]
		apDisplay.printMsg("created stack with stackdbid="+str(stackdata.dbid))
	except:
		apDisplay.printMsg("created stack has no stackdbid")

#-----------------------------------------------------------------------

if __name__ == '__main__':
	# record command line
	#apParam.writeFunctionLog(sys.argv, logfile=".makestacklog")

	# create params dictionary & set defaults
	params = createDefaults()

	# parse command line input
	params = parseInput(sys.argv)

	checkParamConflicts(params)

	# stack must have a description
	if not params['description']:
		apDisplay.printError("Stack must have a description")
		
	if params['selexonId'] is None and params['sessionname'] is not None:
		params['selexonId'] = apParticle.guessParticlesForSession(sessionname=params['sessionname'])

	# get images from database if using a selexon runId
	if params['selexonId']:
		if params['defocpair']:
			images = getImgsDefocPairFromSelexonId(params)
		else:
			images = getImgsFromSelexonId(params)

	# if a runId is specified, outdir will have a subdirectory named runId
	if params['runid']:
		if params['outdir'] is None:
			#/ami/data##/appion/session/stacks/run#
			params['imgdir'] = apDatabase.getImgDir(params['sessionname'])
			outdir = os.path.split(params['imgdir'])[0]
			#change leginon to appion
			outdir = re.sub('leginon','appion',outdir)
			params['outdir'] = os.path.join(outdir, "stacks")
		params['outdir'] = os.path.join(params['outdir'], params['runid'])
		apDisplay.printMsg("output directory: "+params['outdir'])
		#params['rundir'] = os.path.join(params['outdir'], params['runid'])
	apParam.createDirectory(params['outdir'])
	logfile = os.path.join(params['outdir'], "makestack.log")
	os.chdir(params['outdir'])
	apParam.writeFunctionLog(sys.argv, logfile=logfile)

	# if making a single stack, remove existing stack if exists
	if params['single']:
		stackfile=os.path.join(params['outdir'], os.path.splitext(params['single'])[0])
		# if saving to the database, store the stack parameters
		if params['commit']is True:
			insertStackRun(params)
		if params['spider'] is True and os.path.isfile(stackfile+".spi"):
			os.remove(stackfile+".spi")
		if (os.path.isfile(stackfile+".hed")):
			os.remove(stackfile+".hed")
		if (os.path.isfile(stackfile+".img")):
			os.remove(stackfile+".img")
			
		# set up counter for particle log
		p_logfile=os.path.join(params['outdir'], ".particlelog")

 		if (os.path.isfile(p_logfile)):
			os.remove(p_logfile)
		params['particle']=0
		
	# get list of input images, since wildcards are supported
	else:
		if not params['imgs']:
			apDisplay.printError("enter particle images to box or use a particles selection runId")
		imglist=params['imgs']
		images=[]
		for img in imglist:
			imageq = leginondata.AcquisitionImageData(filename=img)
			imageresult = db.query(imageq, readimages=False)
			images += imageresult

		params['session']=images[0]['session']['name']
		params['sessionname']=images[0]['session']['name']
			

	# box particles
	# if any restrictions are set, check the image
	totptcls=0
	count = 0
	#while images:
	for imgdict in images:
		count += 1
 		# get session ID
		params['session'] = images[0]['session']['name']
		params['sessionname'] = imgdict['session']['name']
		params['filepath'] = imgdict['session']['image path']
		imgname = imgdict['filename']

		# first remove any existing boxed files
		stackfile = os.path.join(params['outdir'], imgname)
		for ext in ("hed", "img"):
			if os.path.isfile(stackfile+"."+ext):
				os.remove(stackfile+"."+ext)

		if rejectImage(imgdict, params) is False:
			continue

		# get pixel size
		params['apix'] = apDatabase.getPixelSize(imgdict)

		# box the particles
		totptcls += batchBox(params,imgdict)
		
		if not os.path.isfile(os.path.join(params['outdir'], imgname+".hed")):
			apDisplay.printWarning("no particles were boxed from "+apDisplay.short(imgname)+"\n")
			continue

		# phase flip boxed particles if requested
		if params['phaseFlipped']:
			phaseFlip(imgdict, params) # phase flip stack file
		
		# add boxed particles to a single stack
		if params['single']:
			singleStack(params, imgdict)
		
		# warn if not committing
		if not params['commit']:
			apDisplay.printWarning("not committing results to database, all data will be lost")
			apDisplay.printMsg("to preserve data start script over and add 'commit' flag")

		# limit total particles if limit is specified
		expectedptcles = str(int(float(totptcls)/float(count)*len(images)))
		print str(totptcls)+" total particles so far ("+str(len(images)-count)+" images remain; expect "+\
			expectedptcles+" particles)\n"
		if params['partlimit']:
			if totptcls > params['partlimit']:
				break

		tmpboxfile = os.path.join(params['outdir'], "temporaryParticlesFromDB.box")
		if os.path.isfile(tmpboxfile):
			os.remove(tmpboxfile)
	getStackId(params)
	
	print "Done!"
