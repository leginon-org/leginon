#!/usr/bin/env python

#python
import os
import sys
import time
import math
import numpy
import shutil
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apEMAN
from appionlib import apStackMeanPlot


class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [options]")

		### Ints
		self.parser.add_option("--cluster-id", dest="clusterid", type="int",
			help="clustering stack id", metavar="ID")
		self.parser.add_option("--align-id", dest="alignid", type="int",
			help="alignment stack id", metavar="ID")

		### Floats
		self.parser.add_option("--min-score", "--min-spread", dest="minscore", type="float",
			help="Minimum cross-correlation score or maxlikelihood spread", metavar="#")

		self.parser.add_option("--max-shift", dest="maxshift", type="float",
			help="Maximum shift for aligned particles", metavar="#")

		### Strings
		self.parser.add_option("--class-list-keep", dest="keepclasslist",
			help="list of EMAN style class numbers to include in sub-stack, e.g. --class-list-keep=0,5,3", metavar="#,#")
		self.parser.add_option("--class-list-drop", dest="dropclasslist",
			help="list of EMAN style class numbers to exclude in sub-stack, e.g. --class-list-drop=0,5,3", metavar="#,#")
		self.parser.add_option("--keep-file", dest="keepfile",
			help="File listing which particles to keep, EMAN style 0,1,...", metavar="FILE")

		### True/False
		self.parser.add_option("--save-bad", dest="savebad", default=False,
			help="save discarded particles into a stack", action="store_true")
		self.parser.add_option("--exclude-from", dest="excludefrom", default=False,
			help="converts a keepfile into an exclude file", action="store_true")

	#=====================
	def checkConflicts(self):
		### check and make sure we got a practical shift
		if self.params['maxshift'] is not None and self.params['maxshift'] < 1:
			apDisplay.printError("Maximum shift must be greater than 1")

		### check for missing and duplicate entries
		if self.params['alignid'] is None and self.params['clusterid'] is None:
			apDisplay.printError("Please provide either --cluster-id or --align-id")
		if self.params['alignid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("Please provide only one of either --cluster-id or --align-id")

		### get the stack ID from the other IDs
		if self.params['alignid'] is not None:
			self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignid'])
			self.params['stackid'] = self.alignstackdata['stack'].dbid
		elif self.params['clusterid'] is not None:
			self.clusterstackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.alignstackdata = self.clusterstackdata['clusterrun']['alignstack']
			self.params['stackid'] = self.alignstackdata['stack'].dbid

		### check and make sure we got the stack id
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")

		### check that we have a keep or drop list and not both
		if self.params['keepclasslist'] is None and self.params['dropclasslist'] is None and self.params['keepfile'] is None:
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

		includelist = []
		excludelist = []
		### list of classes to be excluded
		if self.params['dropclasslist'] is not None:
			excludestrlist = self.params['dropclasslist'].split(",")
			for excludeitem in excludestrlist:
				excludelist.append(int(excludeitem.strip()))
		apDisplay.printMsg("Exclude list: "+str(excludelist))

		### list of classes to be included
		if self.params['keepclasslist'] is not None:
			includestrlist = self.params['keepclasslist'].split(",")
			for includeitem in includestrlist:
				includelist.append(int(includeitem.strip()))

		### or read from keepfile
		elif self.params['keepfile'] is not None:
			keeplistfile = open(self.params['keepfile'])
			for line in keeplistfile:
				if self.params['excludefrom'] is True:
					excludelist.append(int(line.strip()))
				else:
					includelist.append(int(line.strip()))
			keeplistfile.close()
		apDisplay.printMsg("Include list: "+str(includelist))

		### get particles from align or cluster stack
		apDisplay.printMsg("Querying database for particles")
		q0 = time.time()
		if self.params['alignid'] is not None:
			alignpartq =  appiondata.ApAlignParticleData()
			alignpartq['alignstack'] = self.alignstackdata
			particles = alignpartq.query()
		elif self.params['clusterid'] is not None:
			clusterpartq = appiondata.ApClusteringParticleData()
			clusterpartq['clusterstack'] = self.clusterstackdata
			particles = clusterpartq.query()
		apDisplay.printMsg("Complete in "+apDisplay.timeString(time.time()-q0))

		### write included particles to text file
		includeParticle = []
		excludeParticle = 0
		badscore = 0
		badshift = 0
		badspread = 0
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

			### check shift
			if self.params['maxshift'] is not None:
				shift = math.hypot(alignpart['xshift'], alignpart['yshift'])
				if shift > self.params['maxshift']:
					excludeParticle += 1
					f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
					badshift += 1
					continue


			if self.params['minscore'] is not None:
				### check score
				if ( alignpart['score'] is not None
				 and alignpart['score'] < self.params['minscore'] ):
					excludeParticle += 1
					f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
					badscore += 1
					continue

				### check spread
				if ( alignpart['spread'] is not None
				 and alignpart['spread'] < self.params['minscore'] ):
					excludeParticle += 1
					f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
					badspread += 1
					continue

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
		if badshift > 0:
			apDisplay.printMsg("%d paricles had a large shift"%(badshift))
		if badscore > 0:
			apDisplay.printMsg("%d paricles had a low score"%(badscore))
		if badspread > 0:
			apDisplay.printMsg("%d paricles had a low spread"%(badspread))
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
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'], bad=self.params['savebad'])

		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		apStack.averageStack(stack=newstack)
		if self.params['commit'] is True:
			apStack.commitSubStack(self.params)
			newstackid = apStack.getStackIdFromPath(newstack)
			apStackMeanPlot.makeStackMeanPlot(newstackid, gridpoints=4)



#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()


