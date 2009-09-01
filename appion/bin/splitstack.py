#!/usr/bin/env python

import os
import sys
import random
import math
import appiondata
import shutil
import apStack
import apParam
import apDisplay
import appionScript

class SplitStack(appionScript.AppionScript):
	def setupParserOptions(self):
		print "splitstack.py stackid=<DEF_id> [nptcls=<n> logsplit=<start>,<divisions>] stackname=<stackfile> [commit] rundir=<path>"
		self.params={}
		self.params['nptcls']=None
		self.params['logsplit']=False
		self.params['commit']=True
		self.params['stackname']='start.hed'
		self.params['description']=''
		self.params['rundir'] = None

	def parseParams():
		for arg in args:
			elements=arg.split('=')
			if elements[0]=='stackid':
				self.params['stackid']=int(elements[1])
			elif elements[0]=='commit':
				self.params['commit']=True
			elif elements[0]=='nptcls':
				self.params['nptcls']=int(elements[1])
				self.params['logsplit']=False
			elif elements[0]=='stackname':
				self.params['stackname']=elements[1]
			elif elements[0]=='logsplit':
				subelements=elements[1].split(',')
				self.params['logsplit']=True
				self.params['logstart']=int(subelements[0])
				self.params['logdivisions']=int(subelements[1])
			elif elements[0]=='rundir':
				self.params['rundir']=elements[1]
			elif arg=='nocommit':
				self.params['commit']=False
			elif arg=='commit':
				self.params['commit']=True
			elif elements[0]=='description':
				self.params['description']=elements[1]
			else:
				apDisplay.printError(arg+" is not recognized as a valid parameter")

	def checkConflicts(self):
		if self.params['nptcls'] and self.params['logsplit']:
			print "Error: nptcls and logsplit can not be specified at the same time"
			sys.exit()
		if self.self.params['logsplit']:
			if self.self.params['logdivisions'] < 3:
				print "Error: divisions for logsplit must be greater than two"
				sys.exit()

	def printHelp():
		print "Usage:"

		sys.exit()

	def makeRandomLst(self, nptcls,stackdata):
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

	def oldLogSplit(self, start,end,divisions):
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

	def evenLogSplit(self, start, end, power=1.7):
		endlog = int(round(math.log(end)/math.log(power),0))
		startlog = int(round(math.log(start)/math.log(power),0))
		stacklist = []
		for n in range(startlog, endlog, 1):
			numparticles = round(math.pow(power,n),0)
			stacklist.append(int(numparticles))
		apDisplay.printColor("Making stacks of the following sizes: "+str(stacklist), "cyan")
		return(stacklist)

	def start(self):
		#find stack
		stackparticles = apStack.getStackParticlesFromId(self.params['stackid'])

		if self.params['logsplit']:
			#stacklist = oldLogSplit(self.params['logstart'], len(stackparticles), self.params['logdivisions'])
			stacklist = evenLogSplit(self.params['logstart'], len(stackparticles))
		elif self.params['nptcls']:
			stacklist = [self.params['nptcls']]
		else:
			apDisplay.printError("Please specify nptlcs or logsplit")

		oldstackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(oldstackdata['path']['path'], oldstackdata['name'])
		#create run directory
		if self.params['rundir'] is None:
			path = oldstackdata['path']['path']
			path = os.path.split(os.path.abspath(path))[0]
			self.params['rundir'] = path
		apDisplay.printMsg("Out directory: "+self.params['rundir'])

		origdescription=self.params['description']
		for stack in stacklist:
			self.params['description'] = (
				origdescription+
				(" ... split %d particles from original stackid=%d"
				% (stack, self.params['stackid']))
			)
			workingdir = os.path.join(self.params['rundir'], str(stack))

			#check for previously commited stacks
			newstack = os.path.join(workingdir ,self.params['stackname'])
			apStack.checkForPreviousStack(newstack)

			#create rundir and change to that directory
			apDisplay.printMsg("Run directory: "+workingdir)
			apParam.createDirectory(workingdir)
			os.chdir(workingdir)

			#create random list
			lstfile = makeRandomLst(stack, stackparticles, self.params)
			#shutil.copy(lstfile, workingdir)

			#make new stack
			apStack.makeNewStack(oldstack, newstack, lstfile)
			#apStack.makeNewStack(lstfile, self.params['stackname'])

			#commit new stack
			self.params['keepfile'] = os.path.abspath(lstfile)
			self.params['rundir'] = os.path.abspath(workingdir)
			apStack.commitSubStack(self.params)


if __name__ == '__main__':
	splitstack = SplitStack()
	splitstack.start()
	splitstack.close()


