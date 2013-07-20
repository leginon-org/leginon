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
from appionlib import apScriptLog


####
# This is a database connections file with no file functions
# Please keep it this way
####

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
		else:
			apDisplay.printMsg("Rejecting more particles than keeping, not creating a bad stack")
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
	stackq = appiondata.ApStackParticleData()
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
def getImageIdsFromStack(stackid, msg=True):
	if stackid < 1:
		return []
	t0 = time.time()
	stackdata = appiondata.ApStackData.direct_query(stackid)
	stackq=appiondata.ApStackParticleData()
	stackq['stack'] = stackdata
	stackparticledata=stackq.query()
	stackimages = []
	if msg is True:
		apDisplay.printMsg("querying particle images from stackid="+str(stackid)+" on "+time.asctime())
	for sp in stackparticledata:
		spimagedata = sp['particle']['image']
		spimageid = spimagedata.dbid
		if spimageid not in stackimages:
			stackimages.append(spimageid)
	if msg is True:
		apDisplay.printMsg("Found %d images from stackid=%d" % (len(stackimages),stackid))
	return stackimages

#===============
def sortStackParts(a, b):
	if a['particleNumber'] > b['particleNumber']:
		return 1
	else:
		return -1

#===============
def getOneParticleFromStackId(stackid, particlenumber=1, msg=True):
	if msg is True:
		apDisplay.printMsg("querying one stack particle from stackid="+str(stackid)+" on "+time.asctime())
	stackdata=appiondata.ApStackData.direct_query(stackid)
	stackq=appiondata.ApStackParticleData()
	stackq['stack'] = stackdata
	stackq['particleNumber'] = particlenumber
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
	# stack file is not checked in case it is archieved away
	#if not os.path.isfile(stackpath):
	#	apDisplay.printError("Could not find stack file: "+stackpath)
	if msg is True:
		sys.stderr.write("Old stack info: ")
		apDisplay.printColor("'"+stackdata['description']+"'","cyan")
	return stackdata

#===============
def getStackParticle(stackid, partnum, nodie=False):
	if partnum <= 0:
		apDisplay.printMsg("cannot get particle %d from stack %d"%(partnum,stackid))
	#apDisplay.printMsg("getting particle %d from stack %d"%(partnum,stackid))
	stackparticleq = appiondata.ApStackParticleData()
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
def getStackParticleFromData(stackid, partdata, nodie=False):
	stackparticleq = appiondata.ApStackParticleData()
	stackparticleq['stack'] = appiondata.ApStackData.direct_query(stackid)
	stackparticleq['particle'] = partdata
	stackparticledata = stackparticleq.query()
	if not stackparticledata:
		if nodie is True:
			return
		apDisplay.printError("partid="+str(partdata.dbid)+" was not found in stackid="+str(stackid))
	if len(stackparticledata) > 1:
		apDisplay.printError("There's a problem with this stack. More than one particle with the same particledata.")
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
	iterdata = appiondata.ApRefineIterData.direct_query(iterid)
	refrun = iterdata['refineRun'].dbid
	stackid = getStackIdFromRecon(refrun,msg)
	return stackid

#===============
def getStackIdFromRecon(reconrunid, msg=True):
	reconrundata = appiondata.ApRefineRunData.direct_query(reconrunid)
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
	apDisplay.printMsg("file is %s, mem is %s"
		%(apDisplay.bytes(stacksize), apDisplay.bytes(freemem)))
	### from EMAN FAQ: need to have at least 3x as much ram as the size of the file
	memsize = freemem/3.0
	numfrac = int(math.ceil(stacksize/memsize))

	apDisplay.printMsg("file is %s, will be split into %d fractions"
		%(apDisplay.bytes(stacksize), numfrac))

	for i in range(numfrac):
		emancmd = "cenalignint "+stack
		if numfrac > 1:
			emancmd += " frac="+str(i)+"/"+str(numfrac)
		if mask is not None:
			emancmd += " mask="+str(mask)
		if maxshift is not None:
			emancmd += " maxshift="+str(maxshift)
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

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
	stackq['boxsize'] = oldstackdata['boxsize']
	if 'correctbeamtilt' in params.keys():
		stackq['beamtilt_corrected'] = params['correctbeamtilt']
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
		newstackq = appiondata.ApStackParticleData()
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
def commitMaskedStack(params, oldstackparts, newname=False):
	"""
	commit a substack to database

	required params:
		stackid
		description
		commit
		rundir
		mask
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
	stackq['boxsize'] = oldstackdata['boxsize']
	stackq['mask'] = params['mask']
	if 'correctbeamtilt' in params.keys():
		stackq['beamtilt_corrected'] = params['correctbeamtilt']

	## insert now before datamanager cleans up referenced data
	stackq.insert()

	#Insert particles
	apDisplay.printMsg("Inserting stack particles")
	count = 0
	newpartnum = 1
	total = len(oldstackparts)
	for part in oldstackparts:
		count += 1
		if count % 100 == 0:
			sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
			sys.stderr.write(str(count)+" of "+(str(total))+" complete")

		# Insert particle
		newstackq = appiondata.ApStackParticleData()
		newstackq.update(part)
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
	stackdata = getOnlyStackData(stackId, msg=msg)
	if stackdata['boxsize'] is not None:
		### Quicker method
		stackboxsize = stackdata['boxsize']
		return stackboxsize

	### old method
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
	stpartdata = appiondata.ApStackParticleData.direct_query(stpartid)
	tilt = stpartdata['particle']['image']['scope']['stage position']['a']*180.0/math.pi
	return abs(tilt)

#===============
def getStackIdFromPath(stackpath):
	"""
	For a given path find stack id
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
def getStackIdFromRunName(runname, sessionname, msg=True):
	"""
	For a given run name and session name find stack id
	"""
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)

	stackrunq = appiondata.ApStackRunData()
	stackrunq['stackRunName'] = runname
	stackrunq['session'] = sessiondata

	runsinstackq = appiondata.ApRunsInStackData()
	runsinstackq['stackRun'] = stackrunq
	runsindatas = runsinstackq.query()
	if not runsindatas:
		return None

	### remove substacks
	if len(runsindatas) > 1:
		for runsindata in runsindatas:
			if runsindata['stack']['oldstack'] is not None or runsindata['stack']['substackname'] is not None:
				runsindatas.remove(runsindata)

	if len(runsindatas) == 1:
		### simpe case
		stackid = runsindatas[0]['stack'].dbid
	else:
		for runsindata in runsindatas:
			print runsindata
		apDisplay.printError("Found too many stacks for specified criteria")

	apDisplay.printMsg("Found stack id %d with runname %s from session %s"%(stackid, runname, sessionname))
	return stackid

#===============
def getStackIdFromSubStackName(substackname, sessionname, msg=True):
	"""
	For a given run name and session name find stack id
	"""
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)

	stackrunq = appiondata.ApStackRunData()
	stackrunq['session'] = sessiondata

	stackq = appiondata.ApStackData()
	stackq['substackname'] = substackname

	runsinstackq = appiondata.ApRunsInStackData()
	runsinstackq['stackRun'] = stackrunq
	runsinstackq['stack'] = stackq
	runsindatas = runsinstackq.query()
	if not runsindatas:
		return None
	if len(runsindatas) == 1:
		### simpe case
		stackid = runsindatas[0]['stack'].dbid
	else:
		for runsindata in runsindatas:
			print runsindata
		apDisplay.printError("Found too many sub-stacks for specified criteria")

	apDisplay.printMsg("Found stack id %d with substackname %s from session %s"%(stackid, substackname, sessionname))
	return stackid

#===============
def getNumStacksFromSession(sessionname):
	sessiondata = apDatabase.getSessionDataFromSessionName(sessionname)

	stackrunq = appiondata.ApStackRunData()
	stackrunq['session'] = sessiondata

	runsinstackq = appiondata.ApRunsInStackData()
	runsinstackq['stackRun'] = stackrunq
	runsindatas = runsinstackq.query()

	if not runsindatas:
		return 0
	stacklist = []
	for runsindata in runsindatas:
		stackid = runsindata['stack'].dbid
		if not stackid in stacklist:
			stacklist.append(stackid)
	return len(stacklist)

#===============
def getStackParticleFromParticleId(particleid, stackid, nodie=False):
	"""
	Provided a Stack Id & an ApParticle Id, find the stackparticle Id
	"""
	stackdata = appiondata.ApStackParticleData()
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

	stackpdata = appiondata.ApStackParticleData()
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
	stackpdata = appiondata.ApStackParticleData()
	stackpdata['stack'] = stackdata
	results = stackpdata.query(results=1)
	if results:
		stackp = results[0]
		return apParticle.getParticleDiameter(stackp['particle'])

def getStackRunsFromStack(stackdata):
	runsinstack = getRunsInStack(stackdata.dbid)
	return map((lambda x: x['stackRun']),runsinstack)

#===============
def getExistingRefineStack(stackrefdata,format,phaseflipped,last_part=None,bin=1,lowpass=0,highpass=0):
	refinestackfile = None
	if not last_part:
		# don't query for last_part
		last_part=None
	r = appiondata.ApRefineStackData(stackref=stackrefdata,format=format,phaseflipped=phaseflipped,bin=bin,last_part=last_part,lowpass=lowpass,highpass=highpass).query()
	if r:
		for refinestackdata in r:
			refinestackfile = os.path.join(refinestackdata['preprefine']['path']['path'],refinestackdata['filename'])
			if os.path.isfile(refinestackfile):
				break
		apDisplay.printMsg('Found an existing refinestack of the same format and params: %s' % ( refinestackfile))
	return refinestackfile
		
####
# This is a database connections file with no file functions
# Please keep it this way
####

# Stack is a class to make working with the properties of a stack a bit easier. 
# To use, create an instance of the class eg. stack = Stack(stackid), then access
# any of the properties as needed eg. stack.boxsize. This class uses the "property"
# feature of Python, so don't use the _boxsize attribute. When you all stack.boxsize,
# get_boxsize() is automatically called and if the boxsize has not yet been retrieved
# from the database, it will be done for you.

### For python versions under 3.0, must inherit from object to use property feature
class Stack(object):
    def __init__( self, stackid ):
        
        # Initialize apStackParam properties
        self._stackid       = stackid
        self._stackData     = None
        self._name          = None
        self._path          = None
        self._filePath      = None
        self._description   = None
        self._hidden        = None
        self._substackname  = None
        self._apix          = None
        self._boxsize       = None
        self._numpart       = None
        self._originalStack = None # TODO: turn this into a Stack object
        self._parentStacks  = None

        # Initialize apStackRun properties
        self._boxSize        = None
        self._bin            = None
        self._phaseFlipped   = None
        self._fliptype       = None
        self._aceCutoff      = None
        self._format         = None
        self._inverted       = None
        self._normalized     = None
        self._xmippnorm      = None
        self._defocpair      = None
        self._lowpass        = None
        self._highpass       = None
        self._stackRunName   = None
        
        # Initialize apParticleData params
        self._preset         = None       
        
        # Initialize ScriptParam table params
        self._stackrunlogparams = None
        self._reverse           = None     
        
        # Some table values are NULL, so we need to flag if a table has been checked already
        self.runParamsSet = False   

    
    def setStackDataParams(self):
        if self._stackid is None:
            raise Exception("Trying to access a stack object, but the stackid is not set.")
        
        self.stackData      = getOnlyStackData(self.stackid)
        self.path           = self.stackData['path']['path']
        self.name           = self.stackData['name']
        self.filePath       = os.path.join( self.path, self.name )
        self.description    = self.stackData['description']
        self.hidden         = self.stackData['hidden']
        self.substackname   = self.stackData['substackname'] 
        self.apix           = getStackPixelSizeFromStackId( self.stackid )
        self.boxsize        = getStackBoxsize( self.stackid )
        self.numpart        = getNumberStackParticlesFromId( self.stackid )   
        
        # parent stacks represent the series of sub stacks that went into creating this stack
        # TODO: Does this work? how does it get child stack data???
        self._originalStack = self.stackData
        self.parentStacks = []
        if self.stackData['oldstack']:
            tmpStackData = self.stackData
            while tmpStackData['oldstack']:
                tmpStackData = tmpStackData['oldstack']
                self.parentStacks.append(tmpStackData)  
                
            # Set the original stack created with makestack.py that is the oldest parent of this stack
            self.originalStack = self.parentStacks[-1]           

    def setStackRunDataParams(self):
        # Get more data from the original stack run table
        # TODO: need to handle combined stack
        if self.runParamsSet is True: return
        self.runParamsSet = True
        stackruns = getStackRunsFromStack( self.originalStack )
        stackrun = stackruns[0]
        originalStackParamData = stackrun['stackParams']
        self.boxSize        = originalStackParamData['boxSize']
        self.bin            = originalStackParamData['bin']
        self.phaseFlipped   = originalStackParamData['phaseFlipped']
        self.fliptype       = originalStackParamData['fliptype']
        self.aceCutoff      = originalStackParamData['aceCutoff']
        self.format         = originalStackParamData['fileType']
        self.inverted       = originalStackParamData['inverted']
        self.normalized     = originalStackParamData['normalized']
        self.xmippnorm      = originalStackParamData['xmipp-norm']
        self.defocpair      = originalStackParamData['defocpair']
        self.lowpass        = originalStackParamData['lowpass']
        self.highpass       = originalStackParamData['highpass']
        self.stackRunName   = stackrun['stackRunName']

        
    def setParticleParams(self):
        # Get data from ApParticleData for a single particle from the stack.        
        # Find the preset from AquisitionImageData table
        oneparticle = getOneParticleFromStackId(self.stackid, particlenumber=1)
        preset = oneparticle['particle']['image']['preset']
        if preset:
            presetname = preset['name']
        else:
            presetname = 'manual'
        self.preset = presetname
        
    def setScriptParams(self):
        # Some parameters of a stack are stored in ScriptProgramRun, ScriptParamValue, and ScriptParamName.
        # You basically need to know what you are looking for to see if a param name is in there for a particular 
        # program run.
        self._stackrunlogparams = apScriptLog.getScriptParamValuesFromRunname( self.stackRunName, self.originalStack['path'], jobdata=None )
        self.reverse = 'reverse' in self._stackrunlogparams.keys()

    ### Property Getters
    def get_stackid(self):
        if self._stackid is None:
            raise Exception("Trying to access a stack object, but the stackid is not set.")
        return self._stackid
    
    def get_stackData(self):
        if self._stackData is None: self.setStackDataParams()
        return self._stackData

    def get_path(self):
        if self._path is None: self.setStackDataParams()
        return self._path
    
    def get_name(self):
        if self._name is None: self.setStackDataParams()
        return self._name
    
    def get_filePath(self):
        if self._filePath is None: self.setStackDataParams()
        return self._filePath
    
    def get_description(self):
        if self._description is None: self.setStackDataParams()
        return self._description
    
    def get_hidden(self):
        if self._hidden is None: self.setStackDataParams()
        return self._hidden
    
    def get_substackname(self):
        if self._substackname is None: self.setStackDataParams()
        return self._substackname
    
    def get_apix(self):
        if self._apix is None: self.setStackDataParams()
        return self._apix
    
    def get_boxsize(self):
        if self._boxsize is None: self.setStackDataParams()
        return self._boxsize
    
    def get_numpart(self):
        if self._numpart is None: self.setStackDataParams()
        return self._numpart
    
    def get_originalStack(self):
        if self._originalStack is None: self.setStackDataParams()
        return self._originalStack
    
    def get_parentStacks(self):
        if self._parentStacks is None: self.setStackDataParams()
        return self._parentStacks
    
    def get_boxSize(self):
        if self._boxSize is None: self.setStackRunDataParams()
        return self._boxSize
    
    def get_bin(self):
        if self._bin is None: self.setStackRunDataParams()
        return self._bin
    
    def get_phaseFlipped(self):
        if self._phaseFlipped is None: self.setStackRunDataParams()
        return self._phaseFlipped
    
    def get_fliptype(self):
        if self._fliptype is None: self.setStackRunDataParams()
        return self._fliptype
    
    def get_aceCutoff(self):
        if self._aceCutoff is None: self.setStackRunDataParams()
        return self._aceCutoff
    
    def get_format(self):
        if self._format is None: self.setStackRunDataParams()
        return self._format
    
    def get_inverted(self):
        if self._inverted is None: self.setStackRunDataParams()
        return self._inverted
    
    def get_normalized(self):
        if self._normalized is None: self.setStackRunDataParams()
        return self._normalized
    
    def get_xmippnorm(self):
        if self._xmippnorm is None: self.setStackRunDataParams()
        return self._xmippnorm
    
    def get_defocpair(self):
        if self._defocpair is None: self.setStackRunDataParams()
        return self._defocpair
    
    def get_lowpass(self):
        if self._lowpass is None: self.setStackRunDataParams()
        return self._lowpass
    
    def get_highpass(self):
        if self._highpass is None: self.setStackRunDataParams()
        return self._highpass
    
    def get_stackRunName(self):
        if self._stackRunName is None: self.setStackRunDataParams()
        return self._stackRunName
    
    def get_preset(self):
        if self._preset is None: self.setParticleParams()
        return self._preset
    
    def get_reverse(self):
        if self._reverse is None: self.setScriptParams()
        return self._reverse
    
    ### Property Setters
    def set_stackid(self, stackid): self._stackid = stackid
    def set_stackData(self, stackData): self._stackData = stackData
    def set_path(self, path): self._path = path
    def set_name(self, name): self._name = name
    def set_filePath(self, filePath): self._filePath = filePath
    def set_description(self, description): self._description = description
    def set_hidden(self, hidden): self._hidden = hidden
    def set_substackname(self, substackname): self._substackname = substackname
    def set_apix(self, apix): self._apix = apix
    def set_boxsize(self, boxsize): self._boxsize = boxsize
    def set_numpart(self, numpart): self._numpart = numpart
    def set_originalStack(self, originalStack):self._originalStack = originalStack
    def set_parentStacks(self, parentStacks): self._parentStacks = parentStacks
    def set_boxSize(self, boxSize): self._boxSize = boxSize
    def set_bin(self, bin): self._bin = bin
    def set_phaseFlipped(self, phaseFlipped): self._phaseFlipped = phaseFlipped
    def set_fliptype(self, fliptype): self._fliptype = fliptype
    def set_aceCutoff(self, aceCutoff): self._aceCutoff = aceCutoff
    def set_format(self, format): self._format = format
    def set_inverted(self, inverted): self._inverted = inverted
    def set_normalized(self, normalized): self._normalized = normalized
    def set_xmippnorm(self, xmippnorm): self._xmippnorm = xmippnorm
    def set_defocpair(self, defocpair): self._defocpair = defocpair
    def set_lowpass(self, lowpass): self._lowpass = lowpass
    def set_highpass(self, highpass): self._highpass = highpass
    def set_stackRunName(self, stackRunName): self._stackRunName = stackRunName
    def set_preset(self, preset): self._preset = preset
    def set_reverse(self, reverse): self._reverse = reverse
 
    ### These are the publicly accessable properties of a Stack. 
    stackid         = property( get_stackid, set_stackid, doc="The stackid corresponds to the ref_ID of table apStackData." )
    stackData       = property( get_stackData, set_stackData, doc="The stackid corresponds to the ref_ID of table apStackData." )
    path            = property( get_path, set_path, doc="The path to this stack file. Does not include the file name." )
    name            = property( get_name, set_name, doc="The name of this stack." )
    filePath        = property( get_filePath, set_filePath, doc="The name of this stack." )
    description     = property( get_description, set_description, doc="The name of this stack." )
    hidden          = property( get_hidden, set_hidden, doc="The name of this stack." )
    substackname    = property( get_substackname, set_substackname, doc="The name of this stack." )
    apix            = property( get_apix, set_apix, doc="The name of this stack." )
    boxsize         = property( get_boxsize, set_boxsize, doc="The name of this stack." )
    numpart         = property( get_numpart, set_numpart, doc="The name of this stack." )
    originalStack   = property( get_originalStack, set_originalStack, doc="The name of this stack." )
    parentStacks    = property( get_parentStacks, set_parentStacks, doc="The name of this stack." )
    boxSize         = property( get_boxSize, set_boxSize, doc="The name of this stack." )
    bin             = property( get_bin, set_bin, doc="The name of this stack." )
    phaseFlipped    = property( get_phaseFlipped, set_phaseFlipped, doc="The name of this stack." )
    fliptype        = property( get_fliptype, set_fliptype, doc="The name of this stack." )
    aceCutoff       = property( get_aceCutoff, set_aceCutoff, doc="The name of this stack." )
    format          = property( get_format, set_format, doc="The name of this stack." )
    inverted        = property( get_inverted, set_inverted, doc="The name of this stack." )
    normalized      = property( get_normalized, set_normalized, doc="The name of this stack." )
    xmippnorm       = property( get_xmippnorm, set_xmippnorm, doc="The name of this stack." )
    defocpair       = property( get_defocpair, set_defocpair, doc="The name of this stack." )
    lowpass         = property( get_lowpass, set_lowpass, doc="The name of this stack." )
    highpass        = property( get_highpass, set_highpass, doc="The name of this stack." )
    stackRunName    = property( get_stackRunName, set_stackRunName, doc="The run name of this stack such as stack1-11apr15n37 found in ApStackRunData." )
    preset          = property( get_preset, set_preset, doc="The name of this stack." )
    reverse         = property( get_reverse, set_reverse, doc="True if this stack was made by processing the images in reverse order." )
    
