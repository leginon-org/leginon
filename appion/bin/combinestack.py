#!/usr/bin/python -O

import appionData
import apDB
import os
import sys
import apStack

apdb=apDB.apdb

def createDefaults():
	params={}
	params['stackname']='start.hed'
	params['outdir']=os.getcwd()
	params['description']=''
	params['commit']=False
	params['particleNumber']=1
	return params

def parseParams(args,params):
	for arg in args:
		elements=arg.split('=')
		if elements[0]=='stackids':
			#remember stackids are a list of strings
			stackids=elements[1].split(',')
			params['stackids']=stackids
		elif elements[0]=='stackname':
			params['stackname']=elements[1]
		elif elements[0]=='outdir':
			params['outdir']=elements[1]
		elif elements[0]=='description':
			params['description']=elements[1]
		elif elements[0]=='commit':
			params['commit']=True
		else:
			print elements[0], 'is not recognized as a valid parameter'
			sys.exit()
	return(params)

def checkParams(params):
	if os.path.exists(params['outdir']):
		if os.path.exists(os.path.join(params['outdir'],params['stackname'])):
			print "\n\nA stack with name",params['stackname'],"and path",params['outdir'],"already exists."
			print "Exiting."
			sys.exit()
	else:
		os.makedirs(params['outdir'])	
	return

def printHelp():
	print "\n\nUsage:"
	print 'combinestack.py stackids=<DEF_id>,<DEF_id>,<...> outdir=<path> stackname=<stackfile> description=<"text"> [commit] '
	sys.exit()

def appendToStack(stackdata,params):
	origstackdir=stackdata['path']['path']
	origstackname=stackdata['name']
	newstackdir=params['outdir']
	newstackname=params['stackname']
	command="proc2d %s %s" % (os.path.join(origstackdir,origstackname), os.path.join(newstackdir,newstackname))
	print command
	os.system(command)
	return

def commitStack(stackid,params):
	stackparticlesdata=apStack.getStackFromId(stackid)
	
	newstackq=appionData.ApStackData()
	newstackq['name']=params['stackname']
	newstackq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
	newstackq['description']=params['description']
	
	rinstackdata=apStack.getRunsInStack(stackid)
	for run in rinstackdata:
		newrinstackq=appionData.ApRunsInStackData()
		newrinstackq['stack']=newstackq
		newrinstackq['stackRun']=run['stackRun']
		apdb.insert(newrinstackq)
	
	for particle in stackparticlesdata:
		newstackparticleq=appionData.ApStackParticlesData()
		newstackparticleq['particleNumber']=params['particleNumber']
		newstackparticleq['stack']=newstackq
		newstackparticleq['stackRun']=particle['stackRun']
		newstackparticleq['particle']=particle['particle']
		apdb.insert(newstackparticleq)
		params['particleNumber']+=1
	return
	
	
if __name__=='__main__':
	params=createDefaults()
	if len(sys.argv) < 2:
		printHelp()
	
	params=parseParams(sys.argv[1:],params)
	
	#check for conflicts and set up outdir
	checkParams(params)
	
	#loop through stacks
	for stack in params['stackids']:
		stackid=int(stack)
		#find stack
		stackdata=apStack.getOnlyStackData(stackid)
		
		#append stack
		appendToStack(stackdata,params)
		
		if params['commit']:
			#commit stack
			print "Committing new stack particles"
			commitStack(stackid,params)
	print "Done!"
	
