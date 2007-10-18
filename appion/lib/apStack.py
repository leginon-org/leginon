# stack functions

import os, sys
import time
import apDB
import apDisplay
import appionData

appiondb=apDB.apdb

def makeNewStack(lstfile,newstackname):
	#first remove old imagic stack
	if os.path.exists(newstackname):
		apDisplay.printWarning("removing old stack: "+newstackname)
		time.sleep(2)
		prefix=newstackname.split('.')[0]
		os.remove(prefix+'.hed')
		os.remove(prefix+'.img')
	command=('proc2d %s %s' % (lstfile, newstackname))
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
	print "Getting stack data for stack", stackid
	stackdata=appiondb.direct_query(appionData.ApStackData,stackid)
	return(stackdata)

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


