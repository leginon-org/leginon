# stack functions

import os, sys, re
import time
import math
import apDB
import apDatabase
import apEMAN
import apDisplay
import appionData
import numpy

appiondb = apDB.apdb

def makeNewStack(oldstack, newstack, listfile):
	if not os.path.isfile(oldstack):
		apDisplay.printWarning("could not find old stack: "+oldstack)
	if os.path.isfile(newstack):
		apDisplay.printError("new stack already exists: "+newstack)
		#apDisplay.printWarning("removing old stack: "+newstack)
		#time.sleep(2)
		#prefix=newstack.split('.')[0]
		#os.remove(prefix+'.hed')
		#os.remove(prefix+'.img')
	apDisplay.printMsg("creating a newstack\n\t"+newstack+
		"\nfrom the oldstack\n\t"+oldstack+"\nusing list file\n\t"+listfile)
	command=("proc2d "+oldstack+" "+newstack+" list="+listfile)
	apEMAN.executeEmanCmd(command, verbose=True)
	return

#--------
def getStackParticlesFromId(stackid, msg=True):
	t0 = time.time()
	if msg is True:
		apDisplay.printMsg("querying stack particles from stackid="+str(stackid)+" at "+time.asctime())
	stackdata = appiondb.direct_query(appionData.ApStackData, stackid)
	stackq = appionData.ApStackParticlesData()
	stackq['stack'] = stackdata
	stackpartdata = stackq.query()
	if not stackpartdata:
		apDisplay.printWarning("failed to get particles of stackid="+str(stackid))
	if msg is True:
		apDisplay.printMsg("sorting particles")
	stackpartdata.sort(sortStackParts)
	if msg is True:
		apDisplay.printMsg("received "+str(len(stackpartdata))
			+" stack particles in "+apDisplay.timeString(time.time()-t0))
	return stackpartdata

#--------
def sortStackParts(a, b):
	if a['particleNumber'] > b['particleNumber']:
		return 1
	else:
		return -1

#--------
def getOneParticleFromStackId(stackid, msg=True):
	if msg is True:
		apDisplay.printMsg("querying one stack particle from stackid="+str(stackid)+" on "+time.asctime())
	stackdata=appiondb.direct_query(appionData.ApStackData, stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stack'] = stackdata
	stackparticledata=appiondb.query(stackq, results=1)
	return stackparticledata[0]

#--------
def getOnlyStackData(stackid, msg=True):
	if msg is True:
		apDisplay.printMsg("Getting stack data for stackid="+str(stackid))
	stackdata = appiondb.direct_query(appionData.ApStackData,stackid)
	if not stackdata:
		apDisplay.printError("Stack ID: "+str(stackid)+" does not exist in the database")
	stackpath = os.path.join(stackdata['path']['path'], stackdata['name'])
	if not os.path.isfile(stackpath):
		apDisplay.printError("Could not find stack file: "+stackpath)
	if msg is True:
		sys.stderr.write("Old stack info: ")
		apDisplay.printColor("'"+stackdata['description']+"'","cyan")
	return stackdata

#--------
def getStackParticle(stackid, partnum):
	stackparticleq = appionData.ApStackParticlesData()
	stackparticleq['stack'] = appiondb.direct_query(appionData.ApStackData, stackid)
	stackparticleq['particleNumber'] = partnum
	stackparticledata = stackparticleq.query()
	if not stackparticledata:
		apDisplay.printError("partnum="+str(partnum)+" was not found in stackid="+str(stackid))
	if len(stackparticledata) > 1:
		apDisplay.printError("There's a problem with this stack. More than one particle with the same number.")
	return stackparticledata[0]

#--------
def getRunsInStack(stackid):
	stackdata = appiondb.direct_query(appionData.ApStackData, stackid)
	runsinstackq = appionData.ApRunsInStackData()
	runsinstackq['stack'] = stackdata
	runsinstackdata = appiondb.query(runsinstackq)
	return runsinstackdata

#--------
def checkForPreviousStack(stackname, stackpath=None):
	if stackpath is None:
		spath = os.path.dirname(stackname)
	else:
		spath = os.path.abspath(stackpath)
	stackq = appionData.ApStackData()
	stackq['path'] = appionData.ApPathData(path=spath)
	stackq['name'] = os.path.basename(stackname)
	stackdata = appiondb.query(stackq, results=1)
	if stackdata:
		apDisplay.printError("A stack with name "+stackname+" and path "+stackpath+" already exists!")
	return

#--------
def getListFileParticle(line, linenum):
	sline = line.strip()
	if sline == "":
		apDisplay.printWarning("Blank line "+str(linenum)+" in listfile")
		return None
	words = sline.split()
	if len(words) < 1:
		apDisplay.printWarning("Empty line "+str(linenum)+" in listfile")
		return None
	if not re.match("[0-9]+", words[0]):
		apDisplay.printWarning("Line "+str(linenum)+" in listfile is not int: "+str(words[0]))
		return None

	#### Adding 1 to particle #: EMAN stacks start at 0 and appion starts at 1 ###
	particlenum = int(words[0]) + 1

	return particlenum

#--------
def getStackIdFromRecon(reconrunid, msg=True):
	reconrundata = appiondb.direct_query(appionData.ApRefinementRunData, reconrunid)
	if not reconrundata:
		apDisplay.printWarning("Could not find stack id for Recon Run="+str(reconrunid))
		return None
	stackid = reconrundata['stack'].dbid
	if msg is True:
		apDisplay.printMsg("Found Stack id="+str(stackid)+" for Recon Run id="+str(reconrunid))
	return stackid

#--------
def averageStack(stack="start.hed", outfile="average.mrc", msg=True):
	if msg is True:
		apDisplay.printMsg("averaging stack for summary web page")
	stackfile = os.path.abspath(stack)
	if not os.path.isfile(stackfile):
		apDisplay.printWarning("could not create stack average, average.mrc")
		return False
	avgmrc = os.path.join(os.path.dirname(stackfile), outfile)
	emancmd = ( "proc2d "+stackfile+" "+avgmrc+" average" )
	apEMAN.executeEmanCmd(emancmd, verbose=msg)
	return True

#========
def centerParticles(stack):
	apDisplay.printMsg("centering stack: "+stack)
	ext=stack.split('.')[-1]
	fsize = os.stat(stack)[6]
	# if imagic file, use larger img file
	if ext == 'hed':
		fsize = os.stat(re.sub(".hed$",".img",stack))[6]
	# stack will be centered in 2 gb increments, determine how many
	frac = int(math.ceil(fsize/2000000000.0))
	apDisplay.printMsg("file is "+str(fsize)+" bytes, will be split into "+str(frac)+" fractions")
	for i in range(frac):
		emancmd = "cenalignint "+stack
		if frac > 1:
			emancmd += " frac="+str(i)+"/"+str(frac)
		apEMAN.executeEmanCmd(emancmd, verbose=True)
	return
	
#--------
def commitSubStack(params, newname=False):
	"""
	commit a substack to database
	
	required params:
		stackid
		description
		commit
		rundir
		keepfile
	"""

	oldstackdata = getOnlyStackData(params['stackid'], msg=False)

	#create new stack data
	stackq = appionData.ApStackData()
	stackq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	stackq['name'] = oldstackdata['name']

	# use new stack name if provided
	if newname:
		stackq['name'] = newname

	stackdata=appiondb.query(stackq, results=1)

	if stackdata:
		apDisplay.printWarning("A stack with these parameters already exists")
		return
	stackq['oldstack'] = oldstackdata
	stackq['hidden'] = False
	stackq['substackname'] = params['runname']
	stackq['description'] = params['description']

	partinserted = 0
	#Insert particles
	listfile = params['keepfile']
	newparticlenum = 1
	f=open(listfile,'r')
	total = len(f.readlines())
	f.close()
	f=open(listfile,'r')
	apDisplay.printMsg("Inserting stack particles")
	count = 0
	for line in f:
		count += 1
		if count % 100 == 0:
			sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
			sys.stderr.write(str(count)+" of "+(str(total))+" complete")
		particlenum = getListFileParticle(line, newparticlenum)
		if particlenum is None:
			continue

		# Find corresponding particle in old stack
		oldstackpartdata = getStackParticle(params['stackid'], particlenum)

		#is this going to work???
		#oldstackpartdata['stackRun']['stackRunName'] = params['runname']
		# Insert particle
		newstackq = appionData.ApStackParticlesData()
		newstackq['particleNumber'] = newparticlenum
		newstackq['stack'] = stackq
		newstackq['stackRun'] = oldstackpartdata['stackRun']
		newstackq['particle'] = oldstackpartdata['particle']
		if params['commit'] is True:
			appiondb.insert(newstackq)
		newparticlenum += 1
	f.close()
	sys.stderr.write("\n")
	if newparticlenum == 0:
		apDisplay.printError("No particles were inserted for the stack")

	apDisplay.printMsg("Inserted "+str(newparticlenum-1)+" stack particles into the database")

	apDisplay.printMsg("Inserting Runs in Stack")
	runsinstack = getRunsInStack(params['stackid'])
	for run in runsinstack:
		newrunsq = appionData.ApRunsInStackData()
		newrunsq['stack'] = stackq
		newrunsq['stackRun'] = run['stackRun']
		if params['commit'] is True:
			appiondb.insert(newrunsq)
		else:
			apDisplay.printWarning("Not commiting to the database")

	apDisplay.printMsg("finished")
	return

def getStackPixelSizeFromStackId(stackId):
	"""
	For a given stack id return stack apix

	Not tested on defocal pairs
	"""
	apDisplay.printWarning("Getting stack pixel size from DB, not tested on defocal pairs")
	stackpart = getOneParticleFromStackId(stackId, msg=False)
	imgapix = apDatabase.getPixelSize(stackpart['particle']['image'])
	runsindata = getRunsInStack(stackId)
	stackbin = runsindata[0]['stackRun']['stackParams']['bin']
	stackapix = imgapix*stackbin
	apDisplay.printMsg("Stack "+str(stackId)+" pixel size: "+str(round(stackapix,3)))
	return stackapix


def getStackBoxsize(stackId):
	"""
	For a given stack id return stack box size

	Not tested on defocal pairs
	"""
	stackpart = getOneParticleFromStackId(stackId, msg=False)
	rawboxsize = stackpart['stackRun']['stackParams']['boxSize']
	runsindata = getRunsInStack(stackId)
	stackbin = runsindata[0]['stackRun']['stackParams']['bin']
	stackboxsize = int(rawboxsize/stackbin)
	apDisplay.printMsg("Stack "+str(stackId)+" box size: "+str(stackboxsize))
	return stackboxsize


def getStackParticleTilt(stpartid):
	"""
	For a given stack part dbid return tilt angle
	"""
	stpartdata = appiondb.direct_query(appionData.ApStackParticlesData, stpartid)
	tilt = stpartdata['particle']['image']['scope']['stage position']['a']*180.0/math.pi
	return abs(tilt)

#########################################################
# Imagic I/O
#########################################################

def readImagic(filename):
	"""
Rudimentary Imagic stack reader
Could be improved with more sophisticated error testing and header parsing
Currently  only reads image data as floats
Currently reads header information for only first image in stack
"""
	root=os.path.splitext(filename)[0]
	headerfilename=root + ".hed"
	datafilename=root + ".img"
	stack={}
	stack['header']=readImagicHeader(headerfilename)
	stack['images']=readImagicData(datafilename, stack['header'])
	return stack
	
def readImagicHeader(headerfilename):
	headfile=open(headerfilename,'rb')
	
	# Header information for each image contained in 256 byte chunks
	# First image header contains all necessary info to read entire stack
	headerbytes=headfile.read(256)
	headfile.close()
	
	i=numpy.fromstring(headerbytes, dtype="Int32")
	f=numpy.fromstring(headerbytes, dtype="Float32")
	
	header={}
	imgnum=i[0]
	imgfollow=i[1]
	header['nimg']=imgnum+imgfollow
	header['npix']=i[11]
	header['lines']=i[12]
	header['rows']=i[13]
	header['avg']=f[17]
	header['sig']=f[18]
	header['max']=f[21]
	header['min']=f[22]

	return header
	
def readImagicData(datafilename, headerdict):
	images=numpy.fromfile(file=datafilename, dtype="Float32")
	images=images.reshape(headerdict['nimg'],headerdict['rows'],headerdict['lines'])
	return images







