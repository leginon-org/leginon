#!/usr/bin/python -O

import os, sys
import appionData
import apStack
import apDB

apdb=apDB.apdb

def scaleStack(stackdata,params):
	origpath=os.path.join(stackdata[0]['stack']['stackPath'],stackdata[0]['stack']['name'])
	newstackpath=os.path.join(params['newstackpath'],params['newstackname'])
	
	if os.path.exists(newstackpath):
		print "Error: A file with the name", params['newstackname']," already exists in this location."
		sys.exit()
		
	bin=params['bin']
	command=('proc2d %s %s shrink=%d' % (origpath,newstackpath,bin))
	os.system(command)
	return

def commitScaledStack(stackdata,params):

	#make new params query
	newstackparamsq=appionData.ApStackParamsData()
	for key in newstackparamsq.keys():
		if key != 'bin':
			newstackparamsq[key]=stackdata[0]['stackRun']['stackParams'][key]
	newstackparamsq['bin']=params['bin']

	#make new stack query
	newstackq=appionData.ApStackData()
	newstackq['stackPath']=params['newstackpath']
	newstackq['name']=params['newstackname']
	newstackq['description']=params['description']
	newstackdata=apdb.query(newstackq)
	
	if newstackdata:
		print "A stack with these parameters already exists"
		return
	
	#make new run query

	#first check that run name doesn't already exist
	newstackrunq=appionData.ApStackRunData()
	newstackrunq['stackRunName'] = os.path.basename(os.getcwd()) #use cwd for run name
	newstackrundata=apdb.query(newstackrunq)
	if newstackrundata:
		print "A stack run with this name (the current directory name) already exists. Exiting"
		sys.exit()
	
	newstackrunq=appionData.ApStackRunData()
	newstackrunq['stackRunName'] = os.path.basename(os.getcwd()) #use cwd for run name
	newstackrunq['stackParams']=newstackparamsq
	newstackrunq['dbemdata|SessionData|session']=stackdata[0]['stackRun']['dbemdata|SessionData|session']
	
	
	#make new runs in stack query and insert also inserts stack and stack run
	newrisq=appionData.ApRunsInStackData()
	newrisq['stack']=newstackq
	newrisq['stackRun']=newstackrunq
	apdb.insert(newrisq)
	
	#loop in reverse order so that order of ptcls in db is like that of orig
	for particle in range(len(stackdata)-1,-1,-1):
		stackparticleq=appionData.ApStackParticlesData()
		stackparticleq['particleNumber']=stackdata[particle]['particleNumber']
		stackparticleq['stack']=newstackq
		stackparticleq['stackRun']=newstackrunq
		stackparticleq['particle']=stackdata[particle]['particle']
		#print stackparticleq
		apdb.insert(stackparticleq)
	return
	

if __name__=='__main__':

	if len(sys.argv) != 4:
		print """Check your arguments
Usage: scalestack.py <stackid> <newstackname> <binning_factor>
---------------------------------------------------------------
scalestack.py will take a stack that has been uploaded to the
appion database and output a new binned stack to the current
directory. The new stack will be commited to the database
"""
		sys.exit()
	
	#parse params
	params={}
	params['stackid']=int(sys.argv[1])
	params['newstackname']=sys.argv[2]
	params['bin']=int(sys.argv[3])
	params['newstackpath']=os.getcwd()
	params['description']="stackid %d was scaled by a factor of %d" % (params['stackid'],params['bin'])
	
	#check for multiple runs in stack
	runs_in_stack=apStack.getRunsInStack(params['stackid'])
	if len(runs_in_stack) > 1:
		print "scalestack.py can't scale this stack because it is a combination of multiple makestack runs."
		print "Instead, use makestack to create a new single scaled stack"
		sys.exit()
		
	#get stackdata
	stackdata=apStack.getStackFromId(params['stackid'])
	
	#do operations on stack
	print "Scaling stack"
	scaleStack(stackdata,params)
	
	#commit new stack to db
	print "Commiting new stack to db"
	commitScaledStack(stackdata,params)
	
	print "Done!"
