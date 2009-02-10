# stack functions

import os, sys, re
import time
import math
import apDatabase
import apEMAN
import apDisplay
import appionData
import apFile
import numpy


#===============
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
	apDisplay.printMsg("creating a new stack\n\t"+newstack+
		"\nfrom the oldstack\n\t"+oldstack+"\nusing list file\n\t"+listfile)
	command=("proc2d "+oldstack+" "+newstack+" list="+listfile)
	apEMAN.executeEmanCmd(command, verbose=True)
	return

#===============
def checkDefocPairFromStackId(stackId):
	# returns True if stack was made with defocal pairs
	runsindata = getRunsInStack(stackId)
	return runsindata[0]['stackRun']['stackParams']['defocpair']
	
	
#===============
def getStackParticlesFromId(stackid, msg=True):
	t0 = time.time()
	if msg is True:
		apDisplay.printMsg("querying stack particles from stackid="+str(stackid)+" at "+time.asctime())
	stackdata = appionData.ApStackData.direct_query(stackid)
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

#===============
def getNumberStackParticlesFromId(stackid, msg=True):
	t0 = time.time()
	stackdata = appionData.ApStackData.direct_query(stackid)
	stackpath = os.path.join(stackdata['path']['path'], stackdata['name'])
	numpart = apFile.numImagesInStack(stackpath)
	return numpart


#===============
def sortStackParts(a, b):
	if a['particleNumber'] > b['particleNumber']:
		return 1
	else:
		return -1

#===============
def getOneParticleFromStackId(stackid, msg=True):
	if msg is True:
		apDisplay.printMsg("querying one stack particle from stackid="+str(stackid)+" on "+time.asctime())
	stackdata=appionData.ApStackData.direct_query(stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stack'] = stackdata
	stackparticledata=stackq.query(results=1)
	if len(stackparticledata) == 0:
		return None
	return stackparticledata[0]

#===============
def getOnlyStackData(stackid, msg=True):
	if msg is True:
		apDisplay.printMsg("Getting stack data for stackid="+str(stackid))
	stackdata = appionData.ApStackData.direct_query(stackid)
	if not stackdata:
		apDisplay.printError("Stack ID: "+str(stackid)+" does not exist in the database")
	stackpath = os.path.join(stackdata['path']['path'], stackdata['name'])
	if not os.path.isfile(stackpath):
		apDisplay.printError("Could not find stack file: "+stackpath)
	if msg is True:
		sys.stderr.write("Old stack info: ")
		apDisplay.printColor("'"+stackdata['description']+"'","cyan")
	return stackdata

#===============
def getStackParticle(stackid, partnum):
	stackparticleq = appionData.ApStackParticlesData()
	stackparticleq['stack'] = appionData.ApStackData.direct_query(stackid)
	stackparticleq['particleNumber'] = partnum
	stackparticledata = stackparticleq.query()
	if not stackparticledata:
		apDisplay.printError("partnum="+str(partnum)+" was not found in stackid="+str(stackid))
	if len(stackparticledata) > 1:
		apDisplay.printError("There's a problem with this stack. More than one particle with the same number.")
	return stackparticledata[0]

#===============
def getRunsInStack(stackid):
	stackdata = appionData.ApStackData.direct_query(stackid)
	runsinstackq = appionData.ApRunsInStackData()
	runsinstackq['stack'] = stackdata
	runsinstackdata = runsinstackq.query()
	return runsinstackdata

#===============
def getSessionDataFromStackId(stackid):
	"""
	For a given stack id return any corresponding session data
	If the stack is a combined stack, it only returns the first session found
	"""
	runsinstackdata = getRunsInStack(stackid)
	if len(runsinstackdata) < 1:
		return None
	sessiondata = runsinstackdata[0]['stackRun']['session']
	return sessiondata

#===============
def checkForPreviousStack(stackname, stackpath=None):
	if stackpath is None:
		spath = os.path.dirname(stackname)
	else:
		spath = os.path.abspath(stackpath)
	stackq = appionData.ApStackData()
	stackq['path'] = appionData.ApPathData(path=spath)
	stackq['name'] = os.path.basename(stackname)
	stackdata = stackq.query(results=1)
	if stackdata:
		apDisplay.printError("A stack with name "+stackname+" and path "+spath+" already exists!")
	return

#===============
def getStackIdFromRecon(reconrunid, msg=True):
	reconrundata = appionData.ApRefinementRunData.direct_query(reconrunid)
	if not reconrundata:
		apDisplay.printWarning("Could not find stack id for Recon Run="+str(reconrunid))
		return None
	stackid = reconrundata['stack'].dbid
	if msg is True:
		apDisplay.printMsg("Found Stack id="+str(stackid)+" for Recon Run id="+str(reconrunid))
	return stackid

#===============
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

#===============
def centerParticles(stack, mask=None, maxshift=None):
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
		if mask is not None:
			emancmd += " mask="+str(mask)
		if maxshift is not None:
			emancmd += " maxshift="+str(maxshift)
		apEMAN.executeEmanCmd(emancmd, verbose=True)
	return
	
#===============
def commitSubStack(params, newname=False, centered=False):
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

	stackdata=stackq.query(results=1)

	if stackdata:
		apDisplay.printWarning("A stack with these parameters already exists")
		return
	stackq['oldstack'] = oldstackdata
	stackq['hidden'] = False
	stackq['substackname'] = params['runname']
	stackq['description'] = params['description']
	stackq['pixelsize'] = oldstackdata['pixelsize']
	stackq['project|projects|project'] = oldstackdata['project|projects|project']
	if centered is True:
		stackq['centered'] = True
		if 'mask' in params:
			stackq['mask'] = params['mask']
		if 'maxshift' in params:
			stackq['maxshift'] = params['maxshift']

	partinserted = 0
	#Insert particles
	listfile = params['keepfile']


	### read list and sort
	f=open(listfile,'r')
	listfilelines = []
	for line in f:
		sline = line.strip()
		if re.match("[0-9]+", sline):
			listfilelines.append(int(sline)+1)
		else:
			apDisplay.printWarning("Line in listfile is not int: "+str(line))
	listfilelines.sort()
	total = len(listfilelines)
	f.close()

	apDisplay.printMsg("Inserting stack particles")
	count = 0
	newpartnum = 1
	for origpartnum in listfilelines:
		count += 1
		if count % 100 == 0:
			sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
			sys.stderr.write(str(count)+" of "+(str(total))+" complete")

		# Find corresponding particle in old stack
		oldstackpartdata = getStackParticle(params['stackid'], origpartnum)

		# Insert particle
		newstackq = appionData.ApStackParticlesData()
		newstackq['particleNumber'] = newpartnum
		newstackq['stack'] = stackq
		newstackq['stackRun'] = oldstackpartdata['stackRun']
		newstackq['particle'] = oldstackpartdata['particle']
		newstackq['mean'] = oldstackpartdata['mean']
		newstackq['stdev'] = oldstackpartdata['stdev']
		if params['commit'] is True:
			newstackq.insert()
		newpartnum += 1
	sys.stderr.write("\n")
	if newpartnum == 0:
		apDisplay.printError("No particles were inserted for the stack")

	apDisplay.printMsg("Inserted "+str(newpartnum-1)+" stack particles into the database")

	apDisplay.printMsg("Inserting Runs in Stack")
	runsinstack = getRunsInStack(params['stackid'])
	for run in runsinstack:
		newrunsq = appionData.ApRunsInStackData()
		newrunsq['stack'] = stackq
		newrunsq['stackRun'] = run['stackRun']
		newrunsq['project|projects|project'] = run['project|projects|project']
		if params['commit'] is True:
			newrunsq.insert()
		else:
			apDisplay.printWarning("Not commiting to the database")

	apDisplay.printMsg("finished")
	return

#===============
def getStackPixelSizeFromStackId(stackId):
	"""
	For a given stack id return stack apix

	Not tested on defocal pairs
	"""
	stackdata = getOnlyStackData(stackId, msg=False)
	if stackdata['pixelsize'] is not None:
		### Quicker method
		stackapix = stackdata['pixelsize']*1e10
		apDisplay.printMsg("Stack "+str(stackId)+" pixel size: "+str(round(stackapix,3)))
		return stackapix
	apDisplay.printWarning("Getting stack pixel size from leginon DB, not tested on defocal pairs")
	stackpart = getOneParticleFromStackId(stackId, msg=False)
	imgapix = apDatabase.getPixelSize(stackpart['particle']['image'])
	runsindata = getRunsInStack(stackId)
	stackbin = runsindata[0]['stackRun']['stackParams']['bin']
	stackapix = imgapix*stackbin
	apDisplay.printMsg("Stack "+str(stackId)+" pixel size: "+str(round(stackapix,3)))
	return stackapix

#===============
def getStackBoxsize(stackId):
	"""
	For a given stack id return stack box size

	Not tested on defocal pairs
	"""
	stackpart = getOneParticleFromStackId(stackId, msg=False)
	if stackpart is None:
		return None
	rawboxsize = stackpart['stackRun']['stackParams']['boxSize']
	runsindata = getRunsInStack(stackId)
	stackbin = runsindata[0]['stackRun']['stackParams']['bin']
	stackboxsize = int(rawboxsize/stackbin)
	apDisplay.printMsg("Stack "+str(stackId)+" box size: "+str(stackboxsize))
	return stackboxsize

#===============
def getStackParticleTilt(stpartid):
	"""
	For a given stack part dbid return tilt angle
	"""
	stpartdata = appionData.ApStackParticlesData.direct_query(stpartid)
	tilt = stpartdata['particle']['image']['scope']['stage position']['a']*180.0/math.pi
	return abs(tilt)

#===============
def getStackIdFromPath(stackpath):
	"""
	For a given stack part dbid return tilt angle
	"""
	path = os.path.dirname(stackpath)
	name = os.path.basename(stackpath)
	pathq = appionData.ApPathData()
	pathq['path'] = path
	stackq = appionData.ApStackData()
	stackq['name'] = name
	stackq['path'] = pathq
	stackdatas = stackq.query()
	if len(stackdatas) > 1:
		apDisplay.printError("More than one stack has path: "+stackpath)
	return stackdatas[0].dbid



