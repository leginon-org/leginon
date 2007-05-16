#! /usr/bin/env python -O
# stack functions

import os, sys
import apDB
import appionData
import data

apdb=apDB.apdb

def getStackFromId(stackid):
	print "Getting particles for stack", stackid
	stackparamsdata=apdb.direct_query(data.ApStackParamsData, stackid)
	stackq=appionData.ApStackParticlesData()
	stackq['stackparams']=stackparamsdata
	stackdata=apdb.query(stackq)
	return(stackdata)
