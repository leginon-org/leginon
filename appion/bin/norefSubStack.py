#!/usr/bin/env python

#python
import sys
import os
import shutil
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
		self.parser.set_usage("Usage: %prog --norefclass=ID --keep-file=FILE [options]")
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
		self.parser.add_option("--norefclass", dest="norefclassid",
			help="REQUIRED: noref class id", metavar="ID")
		self.parser.add_option("--exclude", dest="exclude",
			help="REQUIRED: classes to exclude in the new stack (1,5,8) following EMAN style in the webviewer", metavar="string")

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
				
		norefRun=norefclassdata['norefRun']
		norefclasspath = norefRun['path']['path']+"/cluster"
		norefname = norefRun['name']

		# creating the keep list		
		keepfile = norefclasspath+"/keepfile.list"
		if os.path.isfile(keepfile):
			apDisplay.printWarning("File %s already exist!!!" % (keepfile))
		self.params['keepfile'] = keepfile

		# get stack size
		stackSize = len(apStack.getStackParticlesFromId(self.params['stackid']))

		# list of classes to be excluded		
		excludelist = self.params['exclude'].split(",")

		# initialize an array the size of the original stack
		excludeParticle = []
		for i in range(stackSize):
			excludeParticle.append(0) 

		# for each of the excluded class
		for exClass in excludelist:
			# correct for the class index from eman to spider
			index = int(exClass)+1
			if len(str(index)) == 1:
				exClass = "000"+str(index)
			elif len(str(index)) == 2:
				exClass = "00"+str(index)
			elif len(str(index)) == 3:
				exClass = "0"+str(index)

			# noref class 
			norefclassfile = norefclasspath+"/classdoc"+exClass+".spi"
			apDisplay.printColor("Excluding the classfile "+ norefclassfile, "red")

			# read noref class index file (Spider file)
			f = open(norefclassfile, "r")
			for line in f.readlines():
				num = line.split()
				if num[0] != ";bat/spi":
					# set flag of excluded particle to 1
					excludeParticle[int(float(num[2]))-1] = 1
			f.close()

		
		kf = open(norefclasspath+"/keepfile.list", "w")

		# print to keep file the particles that are to be kept
		for i in range(stackSize):
			if excludeParticle[i] == 1:
				print "Excluding particle " + str(i)
			else:
				print >>kf, str(i)

		kf.close()			

		#get number of particles
		f = open(keepfile, "r")
		numparticles = len(f.readlines())
		f.close()
		self.params['description'] += ( " ... %d particle substack of stackid %d with class(es) %s being excluded" 
			% (numparticles, self.params['stackid'], self.params['exclude']))
		
		#create the new sub stack
		apStack.makeNewStack(oldstack, newstack, keepfile)
		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		apStack.commitSubStack(self.params)
		apStack.averageStack(stack=newstack)

		command=("rm "+keepfile)
		apEMAN.executeEmanCmd(command, verbose=False)

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

