#!/usr/bin/env python

#python
import os
import sys
import time
import math
import numpy
import shutil
#appion
import sinedon.directq
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
		self.parser.add_option("--write-file", dest='writefile', default=False,
			help="write the substack file to disk", action="store_true")

	def isCL2D(self, alignstackdata):
		return (alignstackdata['alignrun']['cl2drun'] or alignstackdata['alignrun']['xmipp3cl2drun'])

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

		# Issue #3566
		if self.params['minscore'] and self.isCL2D(self.alignstackdata):
			apDisplay.printError("CL2d classification does not output alignment parameters.  Can not use minscore to remove particles.")
		if self.params['maxshift'] and self.isCL2D(self.alignstackdata):
			apDisplay.printError("CL2d classification does not output alignment parameters.  Can not use maxshift to remove particles.")

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
			# DIRECT SQL STUFF
			sqlcmd = "SELECT " + \
				"apd.partnum, " + \
				"apd.xshift, apd.yshift, " + \
				"apd.rotation, apd.mirror, " + \
				"apd.spread, apd.correlation, " + \
				"apd.score, apd.bad, " + \
				"spd.particleNumber, " + \
				"ard.refnum "+ \
				"FROM ApAlignParticleData apd " + \
				"LEFT JOIN ApStackParticleData spd ON " + \
				"(apd.`REF|ApStackParticleData|stackpart` = spd.DEF_id) " + \
				"LEFT JOIN ApAlignReferenceData ard ON" + \
				"(apd.`REF|ApAlignReferenceData|ref` = ard.DEF_id) " + \
				"WHERE `REF|ApAlignStackData|alignstack` = %i"%(self.params['alignid'])
			# These are AlignParticles
			particles = sinedon.directq.complexMysqlQuery('appiondata',sqlcmd)

		elif self.params['clusterid'] is not None:
			clusterpartq = appiondata.ApClusteringParticleData()
			clusterpartq['clusterstack'] = self.clusterstackdata
			# These are ClusteringParticles
			particles = clusterpartq.query()
		apDisplay.printMsg("Completed in %s\n"%(apDisplay.timeString(time.time()-q0)))

		### write included particles to text file
		includeParticle = []
		excludeParticle = 0
		badscore = 0
		badshift = 0
		badspread = 0

		f = open("test.log", "w")
		count = 0
		t0 = time.time()
		apDisplay.printMsg("Parsing particle information")

		# find out if there is alignparticle info:
		is_cluster_p = False
		# alignparticle is a key of any particle in particles if the latter is
		# a CluateringParticle
		if 'alignparticle' in particles[0]:
			is_cluster_p = True

		for part in particles:
			count += 1
			if is_cluster_p:
				# alignpart is an item of ClusteringParticle
				alignpart = part['alignparticle']
				try:
					classnum = int(part['refnum'])-1
				except:
					apDisplay.printWarning("particle %d was not put into any class" % (part['partnum']))
				emanstackpartnum = alignpart['stackpart']['particleNumber']-1
			else:
				# particle has info from AlignedParticle as results of direct query
				alignpart = part
				try:
					classnum = int(alignpart['refnum'])-1
				except:
					apDisplay.printWarning("particle %d was not put into any class" % (part['partnum']))
					classnum = None
				emanstackpartnum = int(alignpart['particleNumber'])-1

			### check shift
			if self.params['maxshift'] is not None:
				shift = math.hypot(alignpart['xshift'], alignpart['yshift'])
				if shift > self.params['maxshift']:
					excludeParticle += 1
					if classnum is not None:
						f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
					else:
						f.write("%d\t%d\texclude\n"%(count, emanstackpartnum))
					badshift += 1
					continue

			if self.params['minscore'] is not None:
				### check score
				if ( alignpart['score'] is not None
				 and alignpart['score'] < self.params['minscore'] ):
					excludeParticle += 1
					if classnum is not None:
						f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
					else:
						f.write("%d\t%d\texclude\n"%(count, emanstackpartnum))
					badscore += 1
					continue

				### check spread
				if ( alignpart['spread'] is not None
				 and alignpart['spread'] < self.params['minscore'] ):
					excludeParticle += 1
					if classnum is not None:
						f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
					else:
						f.write("%d\t%d\texclude\n"%(count, emanstackpartnum))
					badspread += 1
					continue

			if classnum is not None:
				if includelist and (classnum in includelist):
					includeParticle.append(emanstackpartnum)
					f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
				elif excludelist and not (classnum in excludelist):
					includeParticle.append(emanstackpartnum)
					f.write("%d\t%d\t%d\tinclude\n"%(count, emanstackpartnum, classnum))
				else:
					excludeParticle += 1
					f.write("%d\t%d\t%d\texclude\n"%(count, emanstackpartnum, classnum))
			else:
				excludeParticle += 1
				f.write("%d\t%d\texclude\n"%(count, emanstackpartnum))
			
		f.close()

		includeParticle.sort()
		if badshift > 0:
			apDisplay.printMsg("%d paricles had a large shift"%(badshift))
		if badscore > 0:
			apDisplay.printMsg("%d paricles had a low score"%(badscore))
		if badspread > 0:
			apDisplay.printMsg("%d paricles had a low spread"%(badspread))
		apDisplay.printMsg("Completed in %s\n"%(apDisplay.timeString(time.time()-t0)))
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding "+str(excludeParticle)+" particles")

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

		outavg = os.path.join(self.params['rundir'],"average.mrc")

		### create the new sub stack
		# first check if virtual stack
		if not os.path.isfile(oldstack):
			vstackdata=apStack.getVirtualStackParticlesFromId(self.params['stackid'])
			vparts = vstackdata['particles']
			oldstack = vstackdata['filename']
			# get subset of virtualstack
			vpartlist = [int(vparts[p]['particleNumber'])-1 for p in includeParticle]
	
			if self.params['writefile'] is True:
				apStack.makeNewStack(oldstack, newstack, vpartlist, bad=self.params['savebad'])

			apStack.averageStack(stack=oldstack,outfile=outavg,partlist=vpartlist)
		else:
			if self.params['writefile'] is True:
				apStack.makeNewStack(oldstack, newstack, self.params['keepfile'], bad=self.params['savebad'])
			apStack.averageStack(stack=oldstack,outfile=outavg,partlist=includeParticle)

		if self.params['writefile'] is True and not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		if self.params['commit'] is True:
			apStack.commitSubStack(self.params,included=includeParticle)
			newstackid = apStack.getStackIdFromPath(newstack)
			apStackMeanPlot.makeStackMeanPlot(newstackid, gridpoints=4)


#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()


