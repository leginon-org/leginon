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
import appionData
import apEMAN
import apStackMeanPlot


class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [options]")

		self.parser.add_option("--cluster-id", dest="clusterid", type="int",
			help="clustering stack id", metavar="ID")
		self.parser.add_option("--align-id", dest="alignid", type="int",
			help="alignment stack id", metavar="ID")

		self.parser.add_option("--class-list-keep", dest="keepclasslist",
			help="list of EMAN style class numbers to include in sub-stack, e.g. --class-list-keep=0,5,3", metavar="#,#")
		self.parser.add_option("--class-list-drop", dest="dropclasslist",
			help="list of EMAN style class numbers to exclude in sub-stack, e.g. --class-list-drop=0,5,3", metavar="#,#")


	#=====================
	def checkConflicts(self):
		if self.params['runname'] is None:
			apDisplay.printError("New stack name was not defined, e.g. --runname=newstack1")

		### check for missing and duplicate entries
		if self.params['alignid'] is None and self.params['clusterid'] is None:
			apDisplay.printError("Please provide either --cluster-id or --align-id")
		if self.params['alignid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("Please provide only one of either --cluster-id or --align-id")		

		### get the stack ID from the other IDs
		if self.params['alignid'] is not None:
			self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignid'])
			self.params['stackid'] = self.alignstackdata['stack'].dbid
		elif self.params['clusterid'] is not None:
			self.clusterstackdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.alignstackdata = clusterstackdata['clusterrun']['alignstack']
			self.params['stackid'] = self.alignstackdata['stack'].dbid

		### check and make sure we got the stack id
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")

		if self.params['keepclasslist'] is None and self.params['dropclasslist'] is None:
			apDisplay.printError("class numbers to be included/excluded was not defined")
		if self.params['keepclasslist'] is not None and self.params['dropclasslist'] is not None:
			apDisplay.printError("both --class-list-keep and --class-list-drop were defined, only one is allowed")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		### new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstack = os.path.join(self.params['rundir'], stackdata['name'])
		apStack.checkForPreviousStack(newstack)

		### list of classes to be excluded
		excludelist = []
		if self.params['dropclasslist'] is not None:
			excludestrlist = self.params['dropclasslist'].split(",")
			for excludeitem in excludestrlist:
				excludelist.append(int(excludeitem.strip()))
		apDisplay.printMsg("Exclude list: "+str(excludelist))

		### list of classes to be included
		includelist = []
		if self.params['keepclasslist'] is not None:
			includestrlist = self.params['keepclasslist'].split(",")
			for includeitem in includestrlist:
				includelist.append(int(includeitem.strip()))		
		apDisplay.printMsg("Include list: "+str(includelist))

		### get particles from align or cluster stack
		if self.params['alignid'] is not None:
			alignpartq =  appionData.ApAlignParticlesData()
			alignpartq['alignstack'] = self.alignstackdata
			particles = alignpartq.query()
		elif self.params['clusterid'] is not None:
			clusterpartq = appionData.ApClusteringParticlesData()
			clusterpartq['clusterstack'] = self.clusterstackdata
			particles = clusterpartq.query()

		### write included particles to text file
		includeParticle = []
		excludeParticle = 0
		f = open("test.log", "w")
		count = 0
		for part in particles:
			count += 1
			#partnum = part['partnum']-1
			if 'alignparticle' in part:
				alignpart = part['alignparticle']
				classnum = int(part['refnum'])-1
			else:
				alignpart = part
				classnum = int(part['ref']['refnum'])-1
			emanstackpartnum = alignpart['stackpart']['particleNumber']-1

			if includelist and classnum in includelist:
				includeParticle.append(emanstackpartnum)
				f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
			elif excludelist and not classnum in excludelist:
				includeParticle.append(emanstackpartnum)
				f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
			else:
				excludeParticle += 1
				f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))

		f.close()
		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding "+str(excludeParticle)+" particles")

		#print includeParticle

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### get number of particles
		numparticles = len(includeParticle)
		if excludelist:
			self.params['description'] += ( " ... %d particle substack with %s classes excluded" 
				% (numparticles, self.params['dropclasslist']))
		elif includelist:
			self.params['description'] += ( " ... %d particle substack with %s classes included" 
				% (numparticles, self.params['keepclasslist']))	

		### create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])

		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		if self.params['commit'] is True:
			apStack.commitSubStack(self.params)
			newstackid = apStack.getStackIdFromPath(newstack)
			apStackMeanPlot.makeStackMeanPlot(newstackid)
		apStack.averageStack(stack=newstack)


#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

