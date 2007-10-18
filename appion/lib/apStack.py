# stack functions

import os, sys
import time
import apDB
import apDisplay
import appionData

appiondb=apDB.apdb

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
	command=("proc2d "+oldstack+" "+newstack+" list="+listfile)
	os.system(command)
	return

def getStackParticlesFromId(stackid):
	print "Getting particles for stack", stackid
	stackdata=appiondb.direct_query(appionData.ApStackData, stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stack']=stackdata
	stackparticledata=appiondb.query(stackq)
	return(stackparticledata)

def getOneParticleFromStackId(stackid):
	print "Getting particles for stack", stackid
	stackdata=appiondb.direct_query(appionData.ApStackData, stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stack'] = stackdata
	stackparticledata=appiondb.query(stackq, results=1)
	return stackparticledata[0]

def getOnlyStackData(stackid):
	apDisplay.printMsg("Getting stack data for stackid="+str(stackid))
	stackdata=appiondb.direct_query(appionData.ApStackData,stackid)
	stackpath = os.path.join(stackdata['path']['path'], stackdata['name'])
	if not os.path.isfile(stackpath):
		apDisplay.printError("Could not find stack file: "+stackpath)
	sys.stderr.write("Old stack info: ")
	apDisplay.printColor("'"+stackdata['description']+"'","cyan")
	return stackdata

def getStackParticle(stackid, particlenumber):
	stackdata=appiondb.direct_query(appionData.ApStackData, stackid)
	stackparticleq=appionData.ApStackParticlesData()
	stackparticleq['stack']=stackdata
	stackparticleq['particleNumber']=particlenumber
	stackparticledata=appiondb.query(stackparticleq)
	if len(stackparticledata) > 1:
		apDisplay.printError("There's a problem with this stack. More than one particle with the same number.")
	return(stackparticledata[0])

def getRunsInStack(stackid):
	stackdata=appiondb.direct_query(appionData.ApStackData, stackid)
	runsinstackq=appionData.ApRunsInStackData()
	runsinstackq['stack']=stackdata
	runsinstackdata=appiondb.query(runsinstackq)
	return(runsinstackdata)


