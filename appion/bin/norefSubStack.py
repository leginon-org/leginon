#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
#appion
import appionScript
import apStack
import apDisplay
import apDB
import appionData
import apEMAN

appiondb = apDB.apdb

class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --norefclass=ID --exclude=0,1,... [options]")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-d", "--description", dest="description", default="",
			help="Stack description", metavar="TEXT")
		self.parser.add_option("-n", "--new-stack-name", dest="runname",
			help="Run id name", metavar="STR")
		self.parser.add_option("--norefclass", dest="norefclassid", type="int",
			help="noref class id", metavar="ID")
		self.parser.add_option("--exclude", dest="exclude",
			help="EMAN style classes to exclude in the new stack (0,5,8)", metavar="0,1,...")

	#=====================
	def checkConflicts(self):
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		if self.params['norefclassid'] is None:
			apDisplay.printError("noref class ID was not defined")
		
		#get the stack ID from the noref class ID
		norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
		norefRun=norefclassdata['norefRun']
		self.params['stackid'] = norefRun['stack'].dbid

		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['exclude'] is None:
			apDisplay.printError("noref classes to be excluded was not defined")

	#=====================
	def setOutDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['outdir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		#new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstack = os.path.join(self.params['outdir'], stackdata['name'])
		apStack.checkForPreviousStack(newstack)

		# using noref class ID to retrieve the noref class data
		norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
				
		norefRun = norefclassdata['norefRun']
		norefclasspath = norefRun['path']['path']+"/cluster"
		norefname = norefRun['name']

		# get stack size
		stackSize = apStack.getNumberStackParticlesFromId(self.params['stackid'])

		# list of classes to be excluded		
		excludestrlist = self.params['exclude'].split(",")
		excludelist = []
		for excld in excludestrlist:
			excludelist.append(int(excld.strip()))

		apDisplay.printMsg("Exclude list: "+str(excludelist))

		#get particles from noref class run
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = norefclassdata
		classpartdatas = classpartq.query()

		includeParticle = []
		excludeParticle = 0
		for classpart in classpartdatas:
			#write to text file
			classnum = classpart['classNumber']-1
			emanstackpartnum = classpart['noref_particle']['particle']['particleNumber']-1
			if not classnum in excludelist:
				includeParticle.append(emanstackpartnum)
			else:
				excludeParticle += 1
		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding "+str(excludeParticle)+" particles")

		#print includeParticle

		### write kept particles to file
		self.params['keepfile'] = os.path.join(norefclasspath, "keepfile-"+self.timestamp+".list")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		#get number of particles
		f = open(keepfile, "r")
		numparticles = len(f.readlines())
		f.close()
		self.params['description'] += ( " ... %d particle substack of stackid %d with class(es) %s being excluded" 
			% (numparticles, self.params['stackid'], self.params['exclude']))
		
		#create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])
		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		apStack.commitSubStack(self.params)
		apStack.averageStack(stack=newstack)

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

