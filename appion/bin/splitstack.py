#!/usr/bin/python -O

import os
import sys
import random
import math
import appionData
import shutil
import apStack
import apParam
import apDisplay

def createDefaults():
	params={}
	params['nptcls']=None
	params['logsplit']=False
	params['commit']=True
	params['stackname']='start.hed'
	params['description']=''
	params['outdir'] = None
	return params

def parseParams(args,params):
	for arg in args:
		elements=arg.split('=')
		if elements[0]=='stackid':
			params['stackid']=int(elements[1])
		elif elements[0]=='commit':
			params['commit']=True
		elif elements[0]=='nptcls':
			params['nptcls']=int(elements[1])
			params['logsplit']=False
		elif elements[0]=='stackname':
			params['stackname']=elements[1]
		elif elements[0]=='logsplit':
			subelements=elements[1].split(',')
			params['logsplit']=True
			params['logstart']=int(subelements[0])
			params['logdivisions']=int(subelements[1])
		elif elements[0]=='outdir':
			params['outdir']=elements[1]
		elif arg=='nocommit':
			params['commit']=False
		elif arg=='commit':
			params['commit']=True
		elif elements[0]=='description':
			params['description']=elements[1]
		else:
			apDisplay.printError(arg+" is not recognized as a valid parameter")
	return params

def checkParams(params):
	if params['nptcls'] and params['logsplit']:
		print "Error: nptcls and logsplit can not be specified at the same time"
		sys.exit()
	if params['logsplit']:
		if params['logdivisions'] < 3:
			print "Error: divisions for logsplit must be greater than two"
			sys.exit()

def printHelp():
	print "Usage:"
	print "splitstack.py stackid=<DEF_id> [nptcls=<n> logsplit=<start>,<divisions>] stackname=<stackfile> [commit] outdir=<path>"
	sys.exit()
	
def makeRandomLst(nptcls,stackdata,params):
	lstfile='temporarylist.lst'
	
	#first remove old lst file
	if os.path.exists(lstfile):
		os.remove(lstfile)
	
	#make random stack
	f=open('temporarylist.lst','w')
	f.write('#LST\n')
	allparticles=range(0,len(stackdata))
	random.shuffle(allparticles)
	particles=allparticles[0:nptcls]
	particles.sort()
	origpath=os.path.join(stackdata[0]['stack']['path']['path'],stackdata[0]['stack']['name'])
	for particle in particles:
		f.write('%d\t%s\n' % (particle, origpath))
	f.close()
	return(lstfile)

def oldLogSplit(start,end,divisions):
	end=math.log(end)
	start=math.log(start)
	incr=(end-start)/divisions
	val=start
	stacklist=[]
	for n in range(0, divisions):
		nptcls=int(round(math.exp(val)))
		stacklist.append(nptcls)
		val+=incr
	apDisplay.printColor("Making stacks of the following sizes: "+str(stacklist), "cyan")
	return(stacklist)

def evenLogSplit(start, end, power=1.7):
	endlog = int(round(math.log(end)/math.log(power),0))
	startlog = int(round(math.log(start)/math.log(power),0))
	stacklist = []
	for n in range(startlog, endlog, 1):
		numparticles = round(math.pow(power,n),0)
		stacklist.append(int(numparticles))
	apDisplay.printColor("Making stacks of the following sizes: "+str(stacklist), "cyan")
	return(stacklist)


if __name__=='__main__':
	params=createDefaults()
	if len(sys.argv) < 2:
		printHelp()

	params=parseParams(sys.argv[1:],params)
	#check for conflicts
	checkParams(params)
	apParam.writeFunctionLog(sys.argv)
	
	#find stack
	stackparticles = apStack.getStackParticlesFromId(params['stackid'])

	if params['logsplit']:
		#stacklist = oldLogSplit(params['logstart'], len(stackparticles), params['logdivisions'])
		stacklist = evenLogSplit(params['logstart'], len(stackparticles))
	elif params['nptcls']:
		stacklist = [params['nptcls']]
	else:
		apDisplay.printError("Please specify nptlcs or logsplit")

	oldstackdata = apStack.getOnlyStackData(params['stackid'])
	oldstack = os.path.join(oldstackdata['path']['path'], oldstackdata['name'])
	#create run directory
	if params['outdir'] is None:
		path = oldstackdata['path']['path']
		path = os.path.split(os.path.abspath(path))[0]
		params['outdir'] = path
	apDisplay.printMsg("Out directory: "+params['outdir'])

	origdescription=params['description']	
	for stack in stacklist:
		params['description'] = (
			origdescription+
			(" ... split %d particles from original stackid=%d" 
			% (stack, params['stackid']))
		)
		workingdir = os.path.join(params['outdir'], str(stack))

		#check for previously commited stacks
		newstack = os.path.join(workingdir ,params['stackname'])
		apStack.checkForPreviousStack(newstack)
		
		#create outdir and change to that directory
		apDisplay.printMsg("Run directory: "+workingdir)
		apParam.createDirectory(workingdir)
		os.chdir(workingdir)

		#create random list 
		lstfile = makeRandomLst(stack, stackparticles, params)
		#shutil.copy(lstfile, workingdir)

		#make new stack
		apStack.makeNewStack(oldstack, newstack, lstfile)
		#apStack.makeNewStack(lstfile, params['stackname'])
		
		#commit new stack
		params['keepfile'] = os.path.abspath(lstfile)
		params['rundir'] = os.path.abspath(workingdir)
		apStack.commitSubStack(params)
	
	apParam.closeFunctionLog()

