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
import apImage

db   = apDB.db
apdb = apDB.apdb

def printHelp():
	print "\nUsage:\nmakestack.py <boxfile> [single=<stackfile>] [outdir=<path>] [ace=<n>] [boxsize=<n>] [inspected or inspectfile=<file>] [bin=<n>] [phaseflip] [noinvert] [spider] mindefocus=<n> maxdefocus=<n> [limit=<n>] [defocpair=<preset>]\n"
	print "Examples:\nmakestack.py extract/001ma.box single=stacks/start.hed ace=0.8 boxsize=180 inspected"
	print "makestack.py extract/*.box outdir=stacks/noctf/ ace=0.8 boxsize=180\n"
	print "* Supports wildcards - By default a stack file of the same name as the box file"
	print "  will be created in the current directory *\n"
	print "<boxfile>            : EMAN box file(s) containing picked particle coordinates"
	print "runid=<runid>        : subdirectory for output (default=stack1)"
	print "                       do not use this option if you are specifying particular images"
	print "outdir=<path>        : Directory in which to create the stack"
	print "single=<file>        : Create a single stack containing all the boxed particles"
	print "                       (density will be inverted)"
	print "ace=<n>              : Only use micrographs with this ACE confidence value and higher"
	print "selexonmin=<n>       : Only use particles of this correlation value and higher"
	print "selexonmax=<n>       : Only use particles of this correlation value and lower"
	print "boxsize=<n>          : Make stacks with this box size (unbinned)"
	print "inspected            : Use only manually inspected images from database"
	print "inspectfile=<file>   : Text file containing results of manually checked images"
	print "phaseflip            : Stack will be phase flipped using best ACE value in database"
	print "bin=<n>              : final images will be binned by this amount"
	print "noinvert             : If writing to a single stack, images will NOT be inverted"
	print "                       (stack images are inverted by default)"
	print "spider               : Single output stack will be in SPIDER format"
	print "mindefocus=<n>       : Limit the defocus to values above what is specified (no limits by default)"
	print "                       Example <mindefocus = -1.0e-6>"
	print "maxdefocus=<n>       : Limit the defocus to values below what is specified (no limits by default)"
	print "                       Example <maxdefocus = -3.0e-6>"
	print "description=\"text\" : description of the stack being created- surround text with double quotes"
	print "prtlrunId=<n>        : use particles from database corresponding to selexon run id"
	print "limit=<n>            : stop boxing particles after total particles gets above limit (no limits by default)"
	print "                     : Example <limit=10000>"
	print "commit               : store particles to database"
	print "sessionname          : name of the session (example: 07jul01c)"
	print "nonorm               : do not normalize images"
	print "medium               : medium of images, carbon or ice (sets noinvert)"
	print "defocpair            : Get particle coords for the focal pair of the image that was picked in runid"
	print "                       For example if your selexon run picked ef images and you specify 'defocpair'"
	print "                       makestack will get the particles from the en images"
	print "uncorrected          : "
	print "\n"
	sys.exit(1)

def createDefaults():
	# create default values for parameters
	params={}
	params["imgs"]=''
	params["runid"]=None
	params["single"]=None
	params["ace"]=None
	params["boxsize"]=None
	params["inspected"]=None
	params['inspectfile']=None
	params["phaseflip"]=False
	params["apix"]=0
	params["kv"]=0
	params["noinvert"]=False
	params["spider"]=False
	params["df"]=0.0
	params['mindefocus']=None
	params['maxdefocus']=None
	params['description']=None
	params['selexonId']=None
	params['sessionnanme']=None
	params['medium']=None
	params['normalize']=True
	params['selexonmin']=None
	params['selexonmax']=None
	params['inspectmask']=None
	params['commit']=False
	params['outdir']=None
	params['particleNumber']=0
	params['bin']=None
	params['limit']=None
	params['defocpair']=False
	params['uncorrected']=False
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
		elif (arg=='phaseflip' or arg=='commit' or arg=='noinvert' or arg=='spider'):
			break
		else:
			boxfile=arg
			if (os.path.exists(boxfile)):
				mrcfileroot.append(os.path.splitext(boxfile)[0])
			else:
				print ("file '%s' does not exist \n" % boxfile)
				sys.exit()
		lastarg+=1
	params["imgs"]=mrcfileroot

	# next get all selection parameters
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='outdir'):
			params['outdir'] = os.path.abspath(elements[1])
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (elements[0]=='single'):
			params["single"]=elements[1]
		elif (elements[0]=='ace'):
			params["ace"]=float(elements[1])
		elif (elements[0]=='selexonmin'):
			params["selexonmin"]=float(elements[1])
		elif (elements[0]=='selexonmax'):
			params["selexonmax"]=float(elements[1])
		elif (elements[0]=='maskassess'):
			params["inspectmask"]=elements[1]
		elif (elements[0]=='boxsize'):
			params["boxsize"]=int(elements[1])
		elif (elements[0]=='inspectfile'):
			params["inspectfile"]=elements[1]
		elif (elements[0]=='medium'):
			params["medium"]=elements[1]
		elif (elements[0]=='bin'):
			params['bin']=int(elements[1])
		elif (elements[0]=='sessionname'):
			params['sessionname']=elements[1]
		elif (arg=='inspected'):
			params["inspected"]=True
		elif (arg=='nonorm'):
			params['normalize']=False
		elif (arg=='phaseflip'):
			params["phaseflip"]=True
		elif (arg=='noinvert'):
			params["noinvert"]=True
		elif (arg=='invert'):
			params["noinvert"]=False
		elif (arg=='spider'):
			params["spider"]=True
		elif (arg=='commit'):
			params['commit']=True
			# if commit is set, must have a runid:
			if not params['runid']:
				params['runid']='stack1'
		elif (elements[0]=='mindefocus'):
			mindf=float(elements[1])
			if mindf > 0:
				print "mindefocus must be negative and specified in meters"
				sys.exit()
			else:
				params['mindefocus']=mindf*1e6
		elif (elements[0]=='maxdefocus'):
			maxdf=float(elements[1])
			if maxdf > 0:
				print "maxdefocus must be negative and specified in meters" 
				sys.exit()
			else:
				params['maxdefocus']=maxdf*1e6
		elif (elements[0]=='description'):
			params["description"]=elements[1]
		elif (elements[0]=='prtlrunId'):
			params["selexonId"]=int(elements[1])
		elif elements[0]=='limit':
			params['limit']=int(elements[1])
		elif arg=='defocpair':
			params['defocpair']=True
		elif arg=='uncorrected':
			params['uncorrected']=True
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
	if (params['commit'] or params['selexonId']) and not params['boxsize']:
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
	f=open(params["inspectfile"],'r')
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
	keep = apDatabase.getImgAssessmentStatus(imgdata)
	if keep is True:
		return True
	return False

def checkPairInspectDB(imgdict,params):
	aq=appionData.ApAssessmentData()
	aq['dbemdata|AcquisitionImageData|image']=params['sibpairs'][imgdict.dbid]
	adata=apdb.query(aq)	

	keep=False
	if adata:
		#check results of only most recent run
		if adata[0]['selectionkeep']==True:
			keep=True
	return(keep)

def batchBox(params, imgdict):
	imgname = imgdict['filename']
	print "processing:",apDisplay.short(imgname)
	if params['uncorrected']:
		tmpname='temporaryCorrectedImage.mrc'
		camera = imgdict['camera']
		dark,norm = apImage.getDarkNorm(params['sessionname'], camera)
		imgarray=apImage.old_correct(imgdict['image'],dark,norm)
		input= os.path.join(params['outdir'],tmpname)
		apImage.arrayToMrc(imgarray,input)
		print "processing", input		
	else:
		input  = os.path.join(params["filepath"], imgname+".mrc")
	output = os.path.join(params["outdir"], imgname+".hed")

	# if getting particles from database, a temporary
	# box file will be created
	if params['selexonId']:
		dbbox=os.path.join(params['outdir'], "temporaryParticlesFromDB.box")
		if params['defocpair']:
			particles,shift=apParticle.getDefocPairParticles(imgdict,params)
		else:
			particles,shift=apParticle.getParticles(imgdict, params['selexonId'])
		if len(particles)>0:			
			###apply limits
			if params['selexonmin'] or params['selexonmax']:
				particles=eliminateMinMaxCCParticles(particles,params)
			
			###apply masks
			if params['inspectmask']:
				particles=eliminateMaskedParticles(particles,params,imgdict)
			
			###save particles
			if len(particles)>0:
				hasparticles=True
				saveParticles(particles,shift,dbbox,params,imgdict)
			else:
				hasparticles=False
		else:
			hasparticles=False
	else:
		dbbox=imgname+".box"
		hasparticles=True
	
	if hasparticles:
		#count number of particles in box file
		f=open(dbbox,'r')
		lines=f.readlines()
		f.close
		nptcls=len(lines)
		# write batchboxer command
		if params["selexonId"]:
			cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i" %(input, dbbox, output, params["boxsize"])
		elif params["boxsize"]:
			cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i insideonly" %(input, dbbox, output, params["boxsize"])
		else: 
	 		cmd="batchboxer input=%s dbbox=%s output=%s insideonly" %(input, dbbox, output)
	
		apDisplay.printMsg("boxing "+str(nptcls)+" particles")
		f=os.popen(cmd)
		f.close()
		return(nptcls)
	else:
		return(0)

	
def eliminateMaskedParticles(particles,params,imgdata):
	newparticles = []
	eliminated = 0
	sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
	maskimg,maskbin = apMask.makeInspectedMask(sessiondata,params['inspectmask'],imgdata)
	if maskimg is not None:
		for prtl in particles:
			binnedcoord = (int(prtl['ycoord']/maskbin),int(prtl['xcoord']/maskbin))
			if maskimg[binnedcoord] != 0:
				eliminated += 1
			else:
				newparticles.append(prtl)
		print eliminated,"particle(s) eliminated due to masking"
	else:
		newparticles = particles
	return newparticles

def eliminateMinMaxCCParticles(particles,params):
	newparticles = []
	eliminated = 0
	for prtl in particles:
		if params['selexonmin'] and prtl['correlation'] < params['selexonmin']:
			eliminated += 1
		elif params['selexonmax'] and prtl['correlation'] > params['selexonmax']:
			eliminated += 1
		else:
			newparticles.append(prtl)
	if eliminated > 0:
		apDisplay.printMsg(str(eliminated)+" particle(s) eliminated due to min or max correlation cutoff")
	return newparticles

def saveParticles(particles,shift,dbbox,params,imgdict):
	imgname = imgdict['filename']
	plist=[]
	box=params['boxsize']
	imgxy=imgdict['camera']['dimension']
	eliminated=0
	for prtl in particles:
		# save the particles to the database
		xcoord=int(math.floor(prtl['xcoord']-(box/2)-shift['shiftx']+0.5))
		ycoord=int(math.floor(prtl['ycoord']-(box/2)-shift['shifty']+0.5))
		if (xcoord>0 and xcoord+box <= imgxy['x'] and ycoord>0 and ycoord+box <= imgxy['y']):
			plist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
			if params['commit']:
				stackpq=appionData.ApStackParticlesData()
				stackpq['stackparams']=params['stackId']
				stackpq['particle']=prtl
				stackres=apdb.query(stackpq)
				if not stackres:
					params['particleNumber']=params['particleNumber']+1
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
	apix    = apDatabase.getPixelSize(imgdata)
	defocus = 1.0e6 * apCtf.getBestDefocusForImage(imgdata)

	if defocus > 0:
		apDisplay.printError("defocus is positive "+str(defocus)+" for image "+shortname)
	elif defocus < -1.0e3:
		apDisplay.printError("defocus is very big "+str(defocus)+" for image "+shortname)
	elif defocus > -1.0e-3:
		apDisplay.printError("defocus is very small "+str(defocus)+" for image "+shortname)

	cmd="applyctf %s %s parm=%f,200,1,0.1,0,17.4,9,1.53,%i,2,%f setparm flipphase" % ( infile,\
	  outfile, defocus, voltage, apix)
	apDisplay.printMsg("phaseflipping particles with defocus "+str(round(defocus,3))+" microns")

	f=os.popen(cmd)
	f.close()

def singleStack(params,imgdict):
	imgname = imgdict['filename']
 	if params['phaseflip'] is True:
		input = os.path.join(params["outdir"], imgname+'.ctf.hed')
	else:
		input = os.path.join(params["outdir"], imgname+'.hed')
	output = os.path.join(params["outdir"], params["single"])

	if params['normalize'] is False:
		cmd="proc2d %s %s" %(input, output)
	else:
		cmd="proc2d %s %s norm=0.0,1.0" %(input, output)

	# bin images is specified
	if params['bin']:
		cmd += " shrink="+str(params['bin'])
		
	# unless specified, invert the images
	if params['noinvert'] is False:
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
	partlogfile = os.path.join(params["outdir"], ".particlelog")
	f = open(partlogfile, 'a')
	for n in range(count-params["particle"]):
		particlenum=str(1+n+params["particle"])
		line = str(particlenum)+'\t'+os.path.join(params['filepath'], imgname+".mrc")
		f.write(line+"\n")
	f.close()
	params["particle"] = count
	
	os.remove(os.path.join(params["outdir"], imgname+".hed"))
	os.remove(os.path.join(params["outdir"], imgname+".img"))
	if params['phaseflip'] is True:
		os.remove(os.path.join(params["outdir"], imgname+".ctf.hed"))
		os.remove(os.path.join(params["outdir"], imgname+".ctf.img"))

# since we're using a batchboxer approach, we must first get a list of
# images that contain particles
def getImgsFromSelexonId(params):
	startt = time.time()
	print "Finding images that have particles for selection run: id="+str(params['selexonId'])

	# get selection run id
	selexonrun=apdb.direct_query(appionData.ApSelectionRunData, params['selexonId'])
	if not (selexonrun):
		apDisplay.printError("specified runId '"+str(params['selexonId'])+"' is not in database")
	
	# from id get the session
	sessionid=db.direct_query(leginondata.SessionData, selexonrun['dbemdata|SessionData|session'])

	# get all images from session
	dbimgq=leginondata.AcquisitionImageData(session=sessionid)
	dbimginfo=db.query(dbimgq, readimages=False)

	if not (dbimginfo):
		apDisplay.printError("no images associated with this runId")

	# for every image, find corresponding image entry in the particle database
	dbimglist=[]
	for img in dbimginfo:
		pimgq = appionData.ApParticleData()
		pimgq['dbemdata|AcquisitionImageData|image'] = img.dbid
		pimgq['selectionrun'] = selexonrun
		pimg = apdb.query(pimgq, results=1)
		if pimg:
			dbimglist.append(img)
	apDisplay.printMsg("completed in "+apDisplay.timeString(time.time()-startt))
	return (dbimglist)

def getImgsDefocPairFromSelexonId(params):
	startt = time.time()
	print "Finding images that have particles for selexon run:", params['selexonId']

	# get selection run id
	selexonrun=apdb.direct_query(appionData.ApSelectionRunData,params['selexonId'])
	if not (selexonrun):
		apDisplay.printError("specified runId '"+str(params['selexonId'])+"' not in database")
	
	# from id get the session
	sessionid=db.direct_query(leginondata.SessionData,selexonrun['dbemdata|SessionData|session'])
	# get all images from session
	dbimgq=leginondata.AcquisitionImageData(session=sessionid)
	dbimginfo=db.query(dbimgq,readimages=False)
	if not (dbimginfo):
		apDisplay.printError("no images associated with this runId")

	# for every image, find corresponding image entry in the particle database
	dbimglist=[]
	params['sibpairs']={}
	for img in dbimginfo:
		pimgq=appionData.ApParticleData()
		pimgq['dbemdata|AcquisitionImageData|image']=img.dbid
		pimgq['selectionrun']=selexonrun
		pimg=apdb.query(pimgq)
		if pimg:
			simgq=appionData.ApImageTransformationData()
			simgq['dbemdata|AcquisitionImageData|image1']=img.dbid
			simgdata=apdb.query(simgq,readimages=False)
			if simgdata:
				simg=simgdata[0]
				siblingimage=db.direct_query(leginondata.AcquisitionImageData,simg['dbemdata|AcquisitionImageData|image2'], readimages=False)
				#create a dictionary for keeping the dbids of image pairs so we don't have to query later
				params['sibpairs'][simg['dbemdata|AcquisitionImageData|image2']] = simg['dbemdata|AcquisitionImageData|image1']
				dbimglist.append(siblingimage)
			else:
				apDisplay.printWarning("no shift data for "+apDisplay.short(img['filename']))
	apDisplay.printMsg("completed in "+apDisplay.timeString(time.time()-startt))
	return (dbimglist)

def insertStackParams(params):
	if params['spider']==True:
		fileType='spider'
	else:
		fileType='imagic'

	if params['noinvert']==True:
		inverted=None
	else:
		inverted=True

	# get stack parameters if they already exist in table
	stparamq=appionData.ApStackParamsData()
	stparamq['stackPath'] = params['outdir']
	stparamq['name']=params['single']

	stackparams=apdb.query(stparamq,results=1)

	# if not in the database, insert new stack parameters
	if not stackparams:
		print "Inserting stack parameters into DB"
		stparamq['description']=params['description']
		stparamq['boxSize']=params['boxsize']
		stparamq['fileType']=fileType
		stparamq['inverted']=inverted
		stparamq['normalized']=params['normalize']
		if params['bin']:
			stparamq['bin']=params['bin']
		if params['phaseflip']==True:
			stparamq['phaseFlipped']=True
		if params['ace']:
			stparamq['aceCutoff']=params['ace']
		if params['selexonmin']:
			stparamq['correlationMin']=params['selexonmin']
		if params['selexonmax']:
			stparamq['correlationMax']=params['selexonmax']
		if params['inspected']:
			stparamq['checkImage']=True
		if params['mindefocus']:
			stparamq['minDefocus']=params['mindefocus']
		if params['maxdefocus']:
			stparamq['maxDefocus']=params['maxdefocus']
			apdb.insert(stparamq)
		stackparams=stparamq
	else:
		stackparams=stackparams[0]
		if (stackparams['description']!=params['description'] or
			stackparams['boxSize']!=params['boxsize'] or
			stackparams['bin']!=params['bin'] or
			stackparams['phaseFlipped']!=params['phaseflip'] or
			stackparams['aceCutoff']!=params['ace'] or
			stackparams['correlationMin']!=params['selexonmin'] or
			stackparams['correlationMax']!=params['selexonmax'] or
			stackparams['checkImage']!=params['inspected'] or
			stackparams['minDefocus']!=params['mindefocus'] or
			stackparams['maxDefocus']!=params['maxdefocus'] or
			stackparams['fileType']!=fileType or
			stackparams['inverted']!=inverted or
			stackparams['normalized']!=params['normalize']):
			apDisplay.printError("All parameters for a particular stack must be identical!"+\
			  "\nplease check your parameter settings.")
	# get the stack Id
	params['stackId']=stackparams


def rejectImage(imgdata, params):
	shortname = apDisplay.short(imgdata['filename'])

	### check if the image has inspected, in file or in database
	if params["inspectfile"] and checkInspectFile(imgdict) is False:
		apDisplay.printColor(shortname+".mrc has been rejected in manual inspection file\n","cyan")
		return False
	if params["inspected"]:
		if params['defocpair'] and checkPairInspectDB(imgdict, params) is False:
			apDisplay.printColor(shortname+".mrc has been rejected by manual defocpair inspection\n","cyan")
			return False
		elif checkInspectDB(imgdict) is False:
			apDisplay.printColor(shortname+".mrc has been rejected by manual inspection\n","cyan")
			return False

	### Get CTF values
	ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)
	
 	if ctfvalue is None:
		if params["ace"] or params['mindefocus'] or params['maxdefocus'] or params['phaseflip']:
			apDisplay.printColor(shortname+".mrc was rejected because it has no ACE values\n","cyan")
			return False
		else:
			apDisplay.printWarning(shortname+".mrc has no ACE values")
			return True
	apCtf.ctfValuesToParams(ctfvalue, params)

	### check that ACE estimation is above confidence threshold
	if params["ace"] and conf < params["ace"]:
			apDisplay.printColor(shortname+".mrc is below ACE threshold (conf="+str(round(conf,3))+")\n","cyan")
			return False
	print conf,"is above",params['ace']

	### skip micrograph that have defocus above or below min & max defocus levels
	if params['mindefocus'] and params['df'] > params['mindefocus']:
		apDisplay.printColor(shortname+".mrc defocus ("+str(round(params['df'],3))+\
			") is less than mindefocus ("+str(params['mindefocus'])+")\n","cyan")
		return False
	if params['maxdefocus'] and params['df'] < params['maxdefocus']:
		apDisplay.printColor(shortname+".mrc defocus ("+str(round(params['df'],3))+\
			") is greater than maxdefocus ("+str(params['maxdefocus'])+")\n","cyan")
		return False

	return True

#-----------------------------------------------------------------------

if __name__ == '__main__':
	# record command line
	apParam.writeFunctionLog(sys.argv, logfile=".makestacklog")

	# create params dictionary & set defaults
	params = createDefaults()

	# parse command line input
	params = parseInput(sys.argv)

	checkParamConflicts(params)

	# stack must have a description
	if not params['description']:
		apDisplay.printError("Stack must have a description")
		
	if params['selexonId'] is None:
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
	apParam.createDirectory(params["outdir"])
	logfile = os.path.join(params['outdir'], "makestack.log")

	# if making a single stack, remove existing stack if exists
	if params["single"]:
		stackfile=os.path.join(params["outdir"], os.path.splitext(params["single"])[0])
		# if saving to the database, store the stack parameters
		if params['commit']is True:
			insertStackParams(params)
		if params["spider"] is True and os.path.isfile(stackfile+".spi"):
			os.remove(stackfile+".spi")
		if (os.path.isfile(stackfile+".hed")):
			os.remove(stackfile+".hed")
		if (os.path.isfile(stackfile+".img")):
			os.remove(stackfile+".img")
			
		# set up counter for particle log
		p_logfile=os.path.join(params["outdir"], ".particlelog")

 		if (os.path.isfile(p_logfile)):
			os.remove(p_logfile)
		params["particle"]=0
		
	# get list of input images, since wildcards are supported
	else:
		if not params['imgs']:
			apDisplay.printError("enter particle images to box or use a particles selection runId")
		imglist=params["imgs"]
		images=[]
		for img in imglist:
			imageq=leginondata.AcquisitionImageData(filename=img)
			imageresult=db.query(imageq, readimages=False)
			images=images+imageresult

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
		stackfile = os.path.join(params["outdir"], imgname)
		for ext in ("hed", "img"):
			if os.path.isfile(stackfile+"."+ext):
				os.remove(stackfile+"."+ext)

		keepimage = rejectImage(imgdict, params)



		if keepimage is False:
			continue

		# box the particles
		totptcls += batchBox(params,imgdict)
		
		if not os.path.isfile(os.path.join(params["outdir"], imgname+".hed")):
			apDisplay.printWarning("no particles were boxed from "+apDisplay.short(imgname)+"\n")
			continue

		# phase flip boxed particles if requested
		if params["phaseflip"]:
			phaseFlip(imgdict, params) # phase flip stack file
		
		# add boxed particles to a single stack
		if params["single"]:
			singleStack(params, imgdict)
		
		# limit total particles if limit is specified
		expectedptcles = str(int(float(totptcls)/float(count)*len(images)))
		print str(totptcls)+" total particles so far ("+str(len(images)-count)+" images remain; expect "+\
			expectedptcles+" particles)\n"
		if params['limit']:
			if totptcls > params['limit']:
				break

		tmpboxfile = os.path.join(params['outdir'], "temporaryParticlesFromDB.box")
		if os.path.isfile(tmpboxfile):
			os.remove(tmpboxfile)


	print "Done!"
