#!/usr/bin/env python

import os
import sys
import time
import glob
import math
import numpy
import shutil
import string
import subprocess
from scipy import stats
#appion libs
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apParam
from appionlib import apImagicFile
from appionlib import apFile
from appionlib import apEMAN
from appionlib import appiondata
from appionlib import apProject
from pyami import mrc

class ccStack(apImagicFile.processStack):
	#=====================
	def getCCValue(self, imgarray1, imgarray2):
		### faster cc, thanks Jim
		ccs = stats.pearsonr(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
		return ccs[0]

	#===============
	def processParticle(self, partarray):
		ccval = self.getCCValue(partarray, self.ccpart)
		str1 = "%05d %05d %.10f\n" % (self.index+1, self.ccindex+1, ccval)
		self.simf.write(str1)
		str2 = "%05d %05d %.10f\n" % (self.ccindex+1, self.index+1, ccval)
		#print "  index2", self.index
		self.simf.write(str2)

class similarityStack(apImagicFile.processStack):
	#===============
	def preLoop(self):
		self.simf = open(self.similarfile, 'w')

	#===============
	def processParticle(self, partarray):
		if self.index == 0:
			return
		#print "index1", self.index
		substack = ccStack(msg=False)
		substack.ccpart = partarray
		substack.simf = self.simf
		substack.ccindex = self.index
		substack.numpart = self.index
		substack.start(self.stackfile)

	#===============
	def postLoop(self):
		self.simf.close()

#=====================
#=====================
class AffinityPropagationClusterScript(appionScript.AppionScript):
	#=====================
	#=====================
	#=====================
	def fillSimilarityMatrix(self, alignedstack):
		### Get initial correlation values
		### this is really, really slow

		similarfile = "similarities.dat"
		simstack = similarityStack()
		simstack.similarfile = similarfile
		simstack.start(alignedstack)

		if not os.path.isfile(similarfile):
			apDisplay.printError("Failed to create similarity file")

		simf = open(similarfile, 'r')
		simlist = []
		count = 0
		for line in simf:
			count += 1
			sline = line.strip()
			slist = sline.split()
			ccval = float(slist[2])
			simlist.append(ccval)
		simf.close()
		apDisplay.printMsg("There are %d lines in the sim file: %s"%(count, similarfile))

		numpart = apFile.numImagesInStack(alignedstack)
		if count != numpart*(numpart-1):
			### we have a valid file already
			apDisplay.printError("There are only %d lines need to have %d"%(count, numpart*(numpart-1)))

		return similarfile, simlist

	#=====================
	#=====================
	#=====================
	def setPreferences(self, simlist):
		print simlist[:5]
		numpart = len(simlist)
		### Preference value stats
		prefarray = numpy.asarray(simlist, dtype=numpy.float32)
		apDisplay.printMsg("CC stats:\n %.5f +/- %.5f\n %.5f <> %.5f"
			%(prefarray.mean(), prefarray.std(), prefarray.min(), prefarray.max()))

		### Determine median preference value
		print self.params['preftype']
		if self.params['preftype'] == 'minlessrange':
			apDisplay.printMsg("Determine minimum minus total range (fewer classes) preference value")
			simarray = numpy.asarray(simlist)
			prefvalue = simarray.min() - (simarray.max() - simarray.min())
		elif self.params['preftype'] == 'minimum':
			apDisplay.printMsg("Determine minimum (few classes) preference value")
			simarray = numpy.asarray(simlist)
			prefvalue = simarray.min()
		else:
			apDisplay.printMsg("Determine median (normal classes) preference value")
			simlist.sort()
			index = int(len(simlist)*0.5)
			medianpref = simlist[index]
			prefvalue = medianpref

		apDisplay.printColor("Final preference value %.6f"%(prefvalue), "cyan")

		### Dumping median preference value
		preffile = 'preferences.dat'
		apDisplay.printMsg("Dumping preference value to file")
		f1 = open(preffile, 'w')
		for i in range(0,numpart):
			f1.write('%.10f\n' % (prefvalue))
		f1.close()

		return preffile

	#=====================
	#=====================
	#=====================
	def runAffinityPropagation(self, alignedstack):
		### Get initial correlation values
		### this is really, really slow
		similarfile, simlist = self.fillSimilarityMatrix(alignedstack)

		### Preference value stats
		preffile = self.setPreferences(simlist)

		### run apcluster.exe program
		outfile = "clusters.out"
		apDisplay.printMsg("Run apcluster.exe program")
		apclusterexe = os.path.join(apParam.getAppionDirectory(), "bin/apcluster.exe")
		apFile.removeFile(outfile)
		clustercmd = apclusterexe+" "+similarfile+" "+preffile+" "+outfile
		clusttime = time.time()
		proc = subprocess.Popen(clustercmd, shell=True)
		proc.wait()
		apDisplay.printMsg("apCluster time: "+apDisplay.timeString(time.time()-clusttime))

		if not os.path.isfile(outfile):
			apDisplay.printError("apCluster did not run")

		### Parse apcluster output file: clusters.out
		apDisplay.printMsg("Parse apcluster output file: "+outfile)
		clustf = open(outfile, "r")
		### each line is the particle and the number is the class
		partnum = 0
		classes = {}
		for line in clustf:
			sline = line.strip()
			if sline:
				partnum += 1
				classnum = int(sline)
				if not classnum in classes:
					classes[classnum] = [partnum,]
				else:
					classes[classnum].append(partnum)
		clustf.close()
		apDisplay.printMsg("Found %d classes"%(len(classes.keys())))

		### Create class averages
		classavgdata = []
		classnames = classes.keys()
		classnames.sort()
		for classnum in classnames:
			apDisplay.printMsg("Class %d, %d members"%(classnum, len(classes[classnum])))
			#clsf = open('subcls%04d.lst'%(classnum), 'w')
			#for partnum in classes[classnum]:
			#	clsf.write("%d\n"%(partnum))
			#clsf.close()
			classdatalist = apImagicFile.readParticleListFromStack(alignedstack, classes[classnum], msg=False)
			classdatarray = numpy.asarray(classdatalist)
			classavgarray = classdatarray.mean(0)
			#mrc.write(classavgarray, 'subcls%04d.mrc'%(classnum))
			classavgdata.append(classavgarray)
		apFile.removeStack("classaverage-"+self.timestamp+".hed")
		apImagicFile.writeImagic(classavgdata, "classaverage-"+self.timestamp+".hed")

		return classes

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --alignid=ID [ --num-part=# ]")

		### integers
		self.parser.add_option("-s", "--alignid", "--alignstack", dest="alignstackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--numpart", dest="numpart", type="int",
			help="Number of particles to use in classification", metavar="#")
		self.parser.add_option("-b", "--bin", dest="bin", type="int", default=1,
			help="Particle binning", metavar="#")
		### floats
		self.parser.add_option("-m", "--mask", "--maskrad", dest="maskrad", type="float",
			help="Mask radius for particle coran (in Angstoms)", metavar="#")
		### choices
		self.prefvalues = ( "median", "minimum", "minlessrange" )
		self.parser.add_option("--preftype", "--preference-type", dest="preftype",
			help="Set preference value type", metavar="TYPE",
			type="choice", choices=self.prefvalues, default="median" )

	#=====================
	def checkConflicts(self):
		if self.params['alignstackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")
		if self.params['maskrad'] is None:
			apDisplay.printError("a mask radius was not provided")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")

	#=====================
	def setRunDir(self):
		self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
		path = self.alignstackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "coran", self.params['runname'])

	#=====================
	def checkAffPropRun(self):
		# create a norefParam object
		clusterrunq = appiondata.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']

		clusterstackq = appiondata.ApClusteringStackData()
		clusterstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterstackq['clusterrun'] = clusterrunq
		# ... path makes the run unique:
		uniquerun = clusterstackq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+self.params['runname']+"' is already in the database")

	#=====================
	def getAlignedStack(self):
		return appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])

	#=====================
	def getNumAlignedParticles(self):
		t0 = time.time()
		self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
		oldalignedstack = os.path.join(self.alignstackdata['path']['path'], self.alignstackdata['imagicfile'])
		numpart = apFile.numImagesInStack(oldalignedstack)
		apDisplay.printMsg("numpart="+str(numpart)+" in "+apDisplay.timeString(time.time()-t0))
		return numpart

	#=====================
	def prepareStack(self):
		### setup box and mask sizes
		self.alignstackdata = self.getAlignedStack()
		maskpixrad = self.params['maskrad']/self.alignstackdata['pixelsize']/self.params['bin']
		boxpixdiam = int(math.ceil(maskpixrad)+1)*2
		if boxpixdiam*self.params['bin'] > self.alignstackdata['boxsize']:
			boxpixdiam = math.floor(self.alignstackdata['boxsize']/self.params['bin'])
		clippixdiam = boxpixdiam*self.params['bin']
		apDisplay.printMsg("Pixel mask radius="+str(maskpixrad))

		### convert aligned stack to local dir
		oldalignedstack = os.path.join(self.alignstackdata['path']['path'], self.alignstackdata['imagicfile'])
		alignedstackname = "alignedstack.hed"
		alignedstack = os.path.join(self.params['rundir'], alignedstackname)
		apFile.removeFile(alignedstack)
		emancmd = ("proc2d %s %s shrink=%d clip=%d,%d"
			%(oldalignedstack,alignedstack,self.params['bin'],clippixdiam,clippixdiam))
		if self.params['numpart'] is not None and self.params['numpart'] < self.numpart:
			emancmd += " last=%d"%(self.params['numpart']-1)
			self.numpart = self.params['numpart']
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		return alignedstack

	#=====================
	#=====================
	#=====================
	def insertAffinityPropagationRun(self, classes):
		### Preliminary data
		numclass = len(classes.keys())
		projectid = apProject.getProjectIdFromAlignStackId(self.params['alignstackid'])
		alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
		pathdata = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))

		### Affinity Propagation Params object
		affpropq = appiondata.ApAffinityPropagationClusterParamsData()
		affpropq['mask_diam'] = 2.0*self.params['maskrad']
		affpropq['run_seconds'] = time.time()-self.t0
		affpropq['preference_type'] = self.params['preftype']

		### Align Analysis Run object
		analysisq = appiondata.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = pathdata
		analysisq['description'] = self.params['description']
		analysisq['alignstack'] = alignstackdata
		analysisq['hidden'] = False
		### linked through cluster not analysis

		### Clustering Run object
		clusterrunq = appiondata.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['description'] = self.params['description']
		clusterrunq['boxsize'] = alignstackdata['boxsize']
		clusterrunq['pixelsize'] = alignstackdata['pixelsize']
		clusterrunq['num_particles'] = self.params['numpart']
		clusterrunq['alignstack'] = alignstackdata
		clusterrunq['analysisrun'] = analysisq
		clusterrunq['affpropparams'] = affpropq

		### Clustering Stack object
		clusterstackq = appiondata.ApClusteringStackData()
		clusterstackq['avg_imagicfile'] = "classaverage-"+self.timestamp+".hed"
		clusterstackq['num_classes'] = numclass
		clusterstackq['clusterrun'] = clusterrunq
		clusterstackq['path'] = pathdata
		clusterstackq['hidden'] = False
		imagicfile = os.path.join(self.params['rundir'], clusterstackq['avg_imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find average stack file: "+imagicfile)

		### looping over clusters
		apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
		for i,classkey in enumerate(classes.keys()):
			classnum = i+1
			partlist = classes[classkey]
			#print "MINIMUM: ", min(partlist)
			classroot = "%s.%d"% (self.timestamp, classnum-1)
			classdocfile = os.path.join(self.params['rundir'], classroot)

			### Clustering Particle object
			clusterrefq = appiondata.ApClusteringReferenceData()
			clusterrefq['refnum'] = classnum
			clusterrefq['clusterrun'] = clusterrunq
			clusterrefq['path'] = pathdata
			clusterrefq['num_particles'] = len(partlist)
			#clusterrefq['ssnr_resolution'] = self.cluster_resolution[i]

			### looping over particles
			sys.stderr.write(".")
			for partnum in partlist:
				alignpartdata = self.getAlignParticleData(partnum, alignstackdata)

				### Clustering Particle objects
				clusterpartq = appiondata.ApClusteringParticleData()
				clusterpartq['clusterstack'] = clusterstackq
				clusterpartq['alignparticle'] = alignpartdata
				clusterpartq['partnum'] = partnum
				clusterpartq['refnum'] = classnum
				clusterpartq['clusterreference'] = clusterrefq

				### finally we can insert parameters
				if self.params['commit'] is True:
					clusterpartq.insert()
		return

	#=====================
	def getAlignParticleData(self, partnum, alignstackdata):
		alignpartq = appiondata.ApAlignParticleData()
		alignpartq['alignstack'] = alignstackdata
		alignpartq['partnum'] = partnum
		alignparts = alignpartq.query(results=1)
		return alignparts[0]

	#=====================
	def start(self):
		self.runtime = 0
		self.checkAffPropRun()
		self.numpart = self.getNumAlignedParticles()
		alignedstack = self.prepareStack()

		### run Affinity Propagation
		aptime = time.time()
		classes = self.runAffinityPropagation(alignedstack)
		aptime = time.time() - aptime

		### insert into database
		inserttime = time.time()
		self.runtime = aptime
		self.insertAffinityPropagationRun(classes)
		inserttime = time.time() - inserttime

		apDisplay.printMsg("Affinity propagation time: "+apDisplay.timeString(aptime))
		apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

if __name__ == '__main__':
	ap = AffinityPropagationClusterScript()
	ap.start()
	ap.close()





