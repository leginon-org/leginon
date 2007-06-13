#!/usr/bin/python -O

import appionData
import apDB
import os
import sys
import random
import EMAN
import math
import apStack

apdb=apDB.apdb

def createDefaults():
	params={}
	params['nptcls']=None
	params['logsplit']=False
	params['stackname']='start.hed'
	params['description']=''
	params['outdir']=os.getcwd()
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
		elif elements[0]=='description':
			params['description']=elements[1]
		else:
			print elements[0], 'is not recognized as a valid parameter'
			sys.exit()
	return(params)

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
	print "splitstack.py stackid=<DEF_id> [nptcls=<n> logsplit] stackname=<stackfile> [commit] outdir=<path>"
	sys.exit()
	
def getNPtcls(stackname):
	return(EMAN.fileCount(stackname)[0])
	
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
	origpath=os.path.join(stackdata[0]['stackparams']['stackPath'],stackdata[0]['stackparams']['name'])
	for particle in particles:
		f.write('%d\t%s\n' % (particle, origpath))
	f.close()
	return(lstfile)

def makeNewStack(lstfile,newstackname):
	#first remove old imagic stack
	if os.path.exists(newstackname):
		print "Warning, removing old stack",newstackname
		prefix=newstackname.split('.')[0]
		os.remove(prefix+'.hed')
		os.remove(prefix+'.img')
	
	command=('proc2d %s %s' % (lstfile, newstackname))
	os.system(command)
	return
	
def checkForPreviousStack(stackpath, stackname):
	stackparamsq=appionData.ApStackParamsData()
	stackparamsq['stackPath']=stackpath
	stackparamsq['name']=stackname
	stackparamsdata=apdb.query(stackparamsq)
	if stackparamsdata:
		print "A stack with path",stackpath, "and name ", stackname, "already exists."
		print "Exiting."
		sys.exit()
	return
	
def commitSplitStack(params, stackdata, lstfile):
	f=open(lstfile,'r')
	f.readline()
	lines=f.readlines()
	f.close()
	
	stackparamsdata=stackdata[0]['stackparams']

	newstackparamsq=appionData.ApStackParamsData()
	for key in newstackparamsq.keys():
		if key not in ['stackPath', 'name','description']:
			newstackparamsq[key]=stackdata[0]['stackparams'][key]
	newstackparamsq['stackPath']=os.getcwd()
	newstackparamsq['name']=params['stackname']
	newstackparamsq['description']=params['description']
	newstackparamsdata=apdb.query(newstackparamsq)
	
	#paranoid double check for previous stacks
	if newstackparamsdata:
		print "A stack with these parameters already exists"
		return
		
	newparticlenumber=1
	for n in lines:
		words=n.split()
		newparticle=int(words[0])
		
		#### Adding 1 to new particle because EMAN stacks start at 0 but appion starts at 1 ###
		newparticle+=1
		
		# Find corresponding particle in old stack
		stackparticleq=appionData.ApStackParticlesData()
		stackparticleq['stackparams']=stackparamsdata
		stackparticleq['particleNumber']=newparticle
		stackparticledata=apdb.query(stackparticleq, results=1)
		#print stackparticledata
		# Insert particles
		
		newstackq=appionData.ApStackParticlesData()
		newstackq['stackparams']=newstackparamsq
		newstackq['particleNumber']=newparticlenumber
		newstackq['particle']=stackparticledata[0]['particle']
		#print newstackq
		apdb.insert(newstackq)
		newparticlenumber+=1

def logSplit(start,end,divisions):
	end=math.log(end)
	start=math.log(start)
	incr=(end-start)/divisions
	val=start
	stacklist=[]
	for n in range(0, divisions):
		nptcls=int(round(math.exp(val)))
		stacklist.append(nptcls)
		val+=incr
	print "Making stacks of the following sizes",stacklist
	return(stacklist)	
	
def createDirectory(newpath):
	if os.path.exists(newpath):
		os.chdir(newpath)
	else:
		os.makedirs(newpath)
		os.chdir(newpath)
	return

if __name__=='__main__':
	params=createDefaults()
	if len(sys.argv) < 2:
		printHelp()

	params=parseParams(sys.argv[1:],params)
	
	#check for conflicts
	checkParams(params)
	
	#find stack
	stackdata=apStack.getStackFromId(params['stackid'])

	if params['logsplit']:
		stacklist=logSplit(params['logstart'],len(stackdata),params['logdivisions'])
	elif params['nptcls']:
		stacklist=[params['nptcls']]
	else:
		print "Error: Please specify nptlcs or logsplit"
		sys.exit()

	origdescription=params['description']	
	for stack in stacklist:
		params['description']=("%s . . . Original stackId %d was split into a stack with %d particles" % (origdescription, params['stackid'], stack))
		workingdir=os.path.join(params['outdir'],str(stack))

		#check for previously commited stacks
		checkForPreviousStack(workingdir,params['stackname'])
		
		#create outdir and change to that directory
		createDirectory(workingdir)

		#create random list 
		lstfile=makeRandomLst(stack,stackdata,params)
		
		#make new stack
		makeNewStack(lstfile,params['stackname'])
		
		#commit new stack
		if params['commit']:
			print "Inserting new stack"
			commitSplitStack(params,stackdata,lstfile)
	
	print "Done!"
