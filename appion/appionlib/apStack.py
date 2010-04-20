# stack functions

import os
import re
import sys
import time
import math
import numpy
### appion
from pyami import mem
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apEMAN
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apFile
from appionlib import apParam
from appionlib import apThread



#===============
def makeNewStack(oldstack, newstack, listfile=None, remove=False, bad=False):
	if not os.path.isfile(oldstack):
		apDisplay.printWarning("could not find old stack: "+oldstack)
	if os.path.isfile(newstack):
		if remove is True:
			apDisplay.printWarning("removing old stack: "+newstack)
			time.sleep(2)
			apFile.removeStack(newstack)
		else:
			apDisplay.printError("new stack already exists: "+newstack)
	apDisplay.printMsg("creating a new stack\n\t"+newstack+
		"\nfrom the oldstack\n\t"+oldstack+"\nusing list file\n\t"+str(listfile))
	emancmd = "proc2d "+oldstack+" "+newstack
	if listfile is not None:
		emancmd += " list="+listfile
	apEMAN.executeEmanCmd(emancmd, verbose=True)
	if bad is True and listfile is not None:
		### run only if num bad particles < num good particles
		newstacknumpart = apFile.numImagesInStack(newstack)
		oldstacknumpart = apFile.numImagesInStack(oldstack)
		if newstacknumpart > oldstacknumpart/2:
			### create bad.hed stack with all bad particles
			badstack = os.path.join(os.path.dirname(newstack), "bad.hed")
			emancmd = "proc2d %s %s exclude=%s"%(oldstack, badstack, listfile)
			apEMAN.executeEmanCmd(emancmd, verbose=True)
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
	stackdata = appiondata.ApStackData.direct_query(stackid)
	stackq = appiondata.ApStackParticlesData()
	stackq['stack'] = stackdata
	stackpartdata = stackq.query(readimages=False)
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
	stackdata = appiondata.ApStackData.direct_query(stackid)
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
	stackdata=appiondata.ApStackData.direct_query(stackid)
	stackq=appiondata.ApStackParticlesData()
	stackq['stack'] = stackdata
	stackparticledata=stackq.query(results=1)
	if len(stackparticledata) == 0:
		return None
	return stackparticledata[0]

#===============
def getOnlyStackData(stackid, msg=True):
	if msg is True:
		apDisplay.printMsg("Getting stack data for stackid="+str(stackid))
	stackdata = appiondata.ApStackData.direct_query(stackid)
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
def getStackParticle(stackid, partnum, nodie=False):
	if partnum <= 0:
		apDisplay.printMsg("cannot get particle %d from stack %d"%(partnum,stackid))
	#apDisplay.printMsg("getting particle %d from stack %d"%(partnum,stackid))
	stackparticleq = appiondata.ApStackParticlesData()
	stackparticleq['stack'] = appiondata.ApStackData.direct_query(stackid)
	stackparticleq['particleNumber'] = partnum
	stackparticledata = stackparticleq.query()
	if not stackparticledata:
		if nodie is True:
			return
		apDisplay.printError("partnum="+str(partnum)+" was not found in stackid="+str(stackid))
	if len(stackparticledata) > 1:
		apDisplay.printError("There's a problem with this stack. More than one particle with the same number.")
	return stackparticledata[0]

#===============
def getRunsInStack(stackid):
	stackdata = appiondata.ApStackData.direct_query(stackid)
	runsinstackq = appiondata.ApRunsInStackData()
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
		spath = stackpath
	stackq = appiondata.ApStackData()
	stackq['path'] = appiondata.ApPathData(path=os.path.abspath(spath))
	stackq['name'] = os.path.basename(stackname)
	stackdata = stackq.query(results=1)
	if stackdata:
		apDisplay.printError("A stack with name "+stackname+" and path "+spath+" already exists!")
	return

#===============
def getStackIdFromIterationId(iterid, msg=True):
	iterdata = appiondata.ApRefinementData.direct_query(iterid)
	refrun = iterdata['refinementRun'].dbid
	stackid = getStackIdFromRecon(refrun)
	return stackid

#===============
def getStackIdFromRecon(reconrunid, msg=True):
	reconrundata = appiondata.ApRefinementRunData.direct_query(reconrunid)
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
	apDisplay.printMsg("Centering stack: "+stack)

	stacksize = apFile.stackSize(stack)
	freemem = mem.free()*1024 #convert memory to bytes
	numproc = apParam.getNumProcessors()
	### from EMAN FAQ: need to have at least 3x as much ram as the size of the file
	memsize = freemem/4.0/numproc #divide by 4 to be safe
	numbits = int(math.ceil(stacksize/memsize))
	numfrac = max(numtwogig, numproc)

	apDisplay.printMsg("file is %s bytes, will be split into %d fractions"
		%(apDisplay.bytes(stacksize), numfrac))

	cmdlist = []
	for i in range(numfrac):
		emancmd = "cenalignint "+stack
		if numfrac > 1:
			emancmd += " frac="+str(i)+"/"+str(numfrac)
		if mask is not None:
			emancmd += " mask="+str(mask)
		if maxshift is not None:
			emancmd += " maxshift="+str(maxshift)
		cmdlist.append(emancmd)

	apThread.threadCommands(cmdlist, numproc, pausetime=3)
	return

#===============
def commitSubStack(params, newname=False, centered=False, oldstackparts=None, sorted=False):
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
	stackq = appiondata.ApStackData()
	stackq['path'] = appiondata.ApPathData(path=os.path.abspath(params['rundir']))
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
	if sorted is True:
		stackq['junksorted'] = True
	if centered is True:
		stackq['centered'] = True
		if 'mask' in params:
			stackq['mask'] = params['mask']
		if 'maxshift' in params:
			stackq['maxshift'] = params['maxshift']

	## insert now before datamanager cleans up referenced data
	stackq.insert()

	partinserted = 0
	#Insert particles
	listfile = params['keepfile']


	### read list and sort
	f=open(listfile,'r')
	listfilelines = []
	for line in f:
		sline = line.strip()
		if re.match("[0-9]+", sline):
			listfilelines.append(int(sline.split()[0])+1)
		else:
			apDisplay.printWarning("Line in listfile is not int: "+str(line))
	listfilelines.sort()
	total = len(listfilelines)
	f.close()

	## index old stack particles by number
	part_by_number = {}
	if oldstackparts is not None:
		for part in oldstackparts:
			part_by_number[part['particleNumber']] = part

	apDisplay.printMsg("Inserting stack particles")
	count = 0
	newpartnum = 1
	for origpartnum in listfilelines:
		count += 1
		if count % 100 == 0:
			sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
			sys.stderr.write(str(count)+" of "+(str(total))+" complete")

		# Find corresponding particle in old stack
		# Use previously queried particles if possible, otherwise
		# do new query here (very slow if millions of prtls in DB)
		try:
			oldstackpartdata = part_by_number[origpartnum]
		except KeyError:
			oldstackpartdata = getStackParticle(params['stackid'], origpartnum)

		# Insert particle
		newstackq = appiondata.ApStackParticlesData()
		newstackq.update(oldstackpartdata)
		newstackq['particleNumber'] = newpartnum
		newstackq['stack'] = stackq
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
		newrunsq = appiondata.ApRunsInStackData()
		newrunsq['stack'] = stackq
		newrunsq['stackRun'] = run['stackRun']
		if params['commit'] is True:
			newrunsq.insert()
		else:
			apDisplay.printWarning("Not commiting to the database")

	apDisplay.printMsg("finished")
	return

#===============
def getStackPixelSizeFromStackId(stackId, msg=True):
	"""
	For a given stack id return stack apix

	Not tested on defocal pairs
	"""
	stackdata = getOnlyStackData(stackId, msg=msg)
	if stackdata['pixelsize'] is not None:
		### Quicker method
		stackapix = stackdata['pixelsize']*1e10
		if msg is True:
			apDisplay.printMsg("Stack "+str(stackId)+" pixel size: "+str(round(stackapix,3)))
		return stackapix
	apDisplay.printWarning("Getting stack pixel size from leginon DB, not tested on defocal pairs")
	stackpart = getOneParticleFromStackId(stackId, msg=msg)
	imgapix = apDatabase.getPixelSize(stackpart['particle']['image'])
	runsindata = getRunsInStack(stackId)
	stackbin = runsindata[0]['stackRun']['stackParams']['bin']
	stackapix = imgapix*stackbin
	if msg is True:
		apDisplay.printMsg("Stack "+str(stackId)+" pixel size: "+str(round(stackapix,3)))
	return stackapix

#===============
def getStackBoxsize(stackId, msg=True):
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
	if msg is True:
		apDisplay.printMsg("Stack "+str(stackId)+" box size: "+str(stackboxsize))
	return stackboxsize

#===============
def getStackParticleTilt(stpartid):
	"""
	For a given stack part dbid return tilt angle
	"""
	stpartdata = appiondata.ApStackParticlesData.direct_query(stpartid)
	tilt = stpartdata['particle']['image']['scope']['stage position']['a']*180.0/math.pi
	return abs(tilt)

#===============
def getStackIdFromPath(stackpath):
	"""
	For a given stack part dbid return tilt angle
	"""
	path = os.path.dirname(stackpath)
	name = os.path.basename(stackpath)
	pathq = appiondata.ApPathData()
	pathq['path'] = path
	stackq = appiondata.ApStackData()
	stackq['name'] = name
	stackq['path'] = pathq
	stackdatas = stackq.query()
	if len(stackdatas) > 1:
		apDisplay.printError("More than one stack has path: "+stackpath)
	return stackdatas[0].dbid

#===============
def getStackParticleFromParticleId(particleid,stackid, nodie=False):
	"""
	Provided a Stack Id & an ApParticle Id, find the stackparticle Id
	"""
	stackdata = appiondata.ApStackParticlesData()
	stackdata['particle'] = appiondata.ApParticleData.direct_query(particleid)
	stackdata['stack'] = appiondata.ApStackData.direct_query(stackid)
	stackpnum = stackdata.query()
	if not stackpnum:
		if nodie is True:
			return
		apDisplay.printError("partnum="+str(particleid)+" was not found in stackid="+str(stackid))
	if len(stackpnum) > 1:
		apDisplay.printError("There's a problem with this stack. More than one particle with the same number.")
	return stackpnum[0]

#===============
def getImageParticles(imagedata,stackid,nodie=True):
	"""
	Provided a Stack Id & imagedata, to find particles
	"""
	particleq = appiondata.ApParticleData(image=imagedata)

	stackpdata = appiondata.ApStackParticlesData()
	stackpdata['particle'] = particleq
	stackpdata['stack'] = appiondata.ApStackData.direct_query(stackid)
	stackps = stackpdata.query()
	particles = []
	if not stackps:
		if nodie is True:
			return particles,None
		apDisplay.printError("partnum="+str(particleid)+" was not found in stackid="+str(stackid))
	for stackp in stackps:
		particles.append(stackp['particle'])
	return particles,stackps

#===============
def findSubStackConditionData(stackdata):
	substackname = stackdata['substackname']
	if not substackname:
		return None,None
	typedict = {
		'alignsub':appiondata.ApAlignStackData(),
		'clustersub':appiondata.ApClusteringStackData(),
	}
	substacktype = None
	for type in typedict.keys():
		if substackname.find(type) >= 0:
			substacktype = type
			break
	if substacktype is None:
		return None,None
	conditionids = re.findall('[0-9]+',substackname)
	q = typedict[substacktype]
	return substacktype,q.direct_query(conditionids[-1])

#===============
def getAlignStack(substacktype,conditionstackdata):
	if substacktype == 'clustersub':
		clusterrundata = conditionstackdata['clusterrun']
		conditionstackdata = clusterrundata['alignstack']
	return conditionstackdata

#===============
def getStackParticleDiameter(stackdata):
	stackpdata = appiondata.ApStackParticlesData()
	stackpdata['stack'] = stackdata
	results = stackpdata.query(results=1)
	if results:
		stackp = results[0]
		return apParticle.getParticleDiameter(stackp['particle'])

