#! /usr/bin/env python -O
# stack functions

import os, sys
import apDB
import appionData

apdb=apDB.apdb

def getStackFromId(stackid):
	print "Getting particles for stack", stackid
	stackdata=apdb.direct_query(appionData.ApStackData, stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stack']=stackdata
	stackparticledata=apdb.query(stackq)
	return(stackparticledata)

def getOnlyStackData(stackid):
	print "Getting stack data for stack", stackid
	stackdata=apdb.direct_query(appionData.ApStackData,stackid)
	return(stackdata)

def getStackParticle(stackid, particlenumber):
	stackdata=apdb.direct_query(appionData.ApStackData, stackid)
	stackparticleq=appionData.ApStackParticlesData()
	stackparticleq['stack']=stackdata
	stackparticleq['particleNumber']=particlenumber
	stackparticledata=apdb.query(stackparticleq)
	if len(stackparticledata) > 1:
		print "There's a problem with this stack. More than one particle with the same number."
		sys.exit()
	return(stackparticledata[0])

def getRunsInStack(stackid):
	stackdata=apdb.direct_query(appionData.ApStackData, stackid)
	runsinstackq=appionData.ApRunsInStackData()
	runsinstackq['stack']=stackdata
	runsinstackdata=apdb.query(runsinstackq)
	return(runsinstackdata)
