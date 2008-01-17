# stack functions

import os, sys, re
import time
import apDB
import apEMAN
import apDisplay
import appionData

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
	apDisplay.printMsg("creating a newstack ("+newstack+
		")\n\tfrom the oldstack ("+oldstack+")")
	command=("proc2d "+oldstack+" "+newstack+" list="+listfile)
	apEMAN.executeEmanCmd(command, verbose=True)
	return

#--------
def getStackParticlesFromId(stackid):
	print "Getting particles for stack", stackid
	stackdata=appiondb.direct_query(appionData.ApStackData, stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stack']=stackdata
	stackparticledata=appiondb.query(stackq)
	return(stackparticledata)

#--------
def getOneParticleFromStackId(stackid):
	print "Getting particles for stack", stackid
	stackdata=appiondb.direct_query(appionData.ApStackData, stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stack'] = stackdata
	stackparticledata=appiondb.query(stackq, results=1)
	return stackparticledata[0]

#--------
def getOnlyStackData(stackid, msg=True):
	apDisplay.printMsg("Getting stack data for stackid="+str(stackid))
	stackdata=appiondb.direct_query(appionData.ApStackData,stackid)
	stackpath = os.path.join(stackdata['path']['path'], stackdata['name'])
	if not os.path.isfile(stackpath):
		apDisplay.printError("Could not find stack file: "+stackpath)
	if msg is True:
		sys.stderr.write("Old stack info: ")
		apDisplay.printColor("'"+stackdata['description']+"'","cyan")
	return stackdata

#--------
def getStackParticle(stackid, particlenumber):
	stackparticleq = appionData.ApStackParticlesData()
	stackparticleq['stack'] = appiondb.direct_query(appionData.ApStackData, stackid)
	stackparticleq['particleNumber'] = particlenumber
	stackparticledata = appiondb.query(stackparticleq)
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
def getStackIdFromRecon(reconrunid):
	reconrundata = appiondb.direct_query(appionData.ApRefinementRunData, reconrunid)
	if not reconrundata:
		apDisplay.printWarning("Could not find stack id for Recon Run="+str(reconrunid))
		return None
	stackid = reconrundata['stack'].dbid
	apDisplay.printMsg("Found Stack id="+str(stackid)+" for Recon Run id="+str(reconrunid))
	return stackid


#--------
def commitSubStack(params):
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
	stackdata=appiondb.query(stackq, results=1)
	if stackdata:
		apDisplay.printWarning("A stack with these parameters already exists")
		return
	stackq['description'] = params['description']

	partinserted = 0
	#Insert particles
	listfile = params['keepfile']
	newparticlenum = 1
	f=open(listfile,'r')
	apDisplay.printMsg("Inserting stack particles")
	for line in f:
		particlenum = getListFileParticle(line, newparticlenum)
		if particlenum is None:
			continue

		# Find corresponding particle in old stack
		oldstackpartdata = getStackParticle(params['stackid'], particlenum)

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



