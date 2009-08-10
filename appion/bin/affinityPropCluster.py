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
import appionScript
import apDisplay
import apParam
import apImagicFile
import apFile
import apEMAN
import appionData
import apProject
from pyami import mrc


#=====================
#=====================
class AffinityPropagationClusterScript(appionScript.AppionScript):
	#=====================
	def getCCValue(self, imgarray1, imgarray2):
		ccs = stats.pearsonr(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
		return ccs[0]

		### old methods follow
		npix = imgarray1.shape[0] * imgarray1.shape[1]

		avg1=imgarray1.mean()
		avg2=imgarray2.mean()

		std1=imgarray1.std()
		var1=std1*std1
		std2=imgarray2.std()
		var2=std2*std2

		### convert 2d -> 1d array and compute dot product
		cc = numpy.dot(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
		cc /= npix
		cc -= (avg1*avg2)
		cc /= math.sqrt(var1*var2)
		return cc

	#=====================
	#=====================
	#=====================
	def fillSimilarityMatrix(self, alignedstack):
		### Get initial correlation values
		### this is really, really slow
		imagicdict = apImagicFile.readImagic(alignedstack)
		partarray = imagicdict['images']
		#print partarray.shape
		numpart = partarray.shape[0]
		boxsize = partarray.shape[1]
		ccmatrix = numpy.ones((numpart, numpart), dtype=numpy.float32)
		#timeper = 27.0e-9
		timeper = 17.0e-9
		apDisplay.printMsg("Computing CC values in about %s"
			%(apDisplay.timeString(timeper*numpart**2*boxsize**2)))
		cctime = time.time()
		if os.path.isfile("cccache.numpy"):
			ccmatrix = numpy.load("cccache.numpy")
		else:
			for i in range(0, numpart):
				for j in range(i+1, numpart):
					ccval = self.getCCValue(partarray[i],partarray[j])
					ccmatrix[i,j] = ccval
					ccmatrix[j,i] = ccval
			ccmatrix.dump("cccache.numpy")
		del partarray
		del imagicdict['images']
		apDisplay.printMsg("CC calc time: %s :: %s per part :: %s per part per pixel"
			%(apDisplay.timeString(time.time()-cctime),
			apDisplay.timeString((time.time()-cctime)/numpart**2),
			apDisplay.timeString((time.time()-cctime)/numpart**2/boxsize**2)))

		### Write similarities
		apDisplay.printMsg("Dumping CC values to file")
		simlist = []
		similarfile = "similarities.dat"
		f1 = open(similarfile, 'w')
		for i in range(0, numpart):
			for j in range(i+1, numpart):
			   str1 = "%d %d %.10f\n" % (i+1, j+1, ccmatrix[i,j])
			   f1.write(str1)
			   str2 = "%d %d %.10f\n" % (j+1, i+1, ccmatrix[j,i])
			   f1.write(str2)
			   simlist.append(ccmatrix[i,j])
		f1.close()

		return similarfile, simlist

	#=====================
	#=====================
	#=====================
	def setPreferences(self, simlist):
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
		self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		path = self.alignstackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "coran", self.params['runname'])

	#=====================
	def checkAffPropRun(self):
		# create a norefParam object
		clusterrunq = appionData.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']

		clusterstackq = appionData.ApClusteringStackData()
		clusterstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterstackq['clusterrun'] = clusterrunq
		# ... path makes the run unique:
		uniquerun = clusterstackq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+self.params['runname']+"' is already in the database")

	#=====================
	def getAlignedStack(self):
		return appionData.ApAlignStackData.direct_query(self.params['alignstackid'])

	#=====================
	def getNumAlignedParticles(self):
		t0 = time.time()
		self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
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
		alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		pathdata = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))

		### Affinity Propagation Params object
		affpropq = appionData.ApAffinityPropagationClusterParamsData()
		affpropq['mask_diam'] = 2.0*self.params['maskrad']
		affpropq['run_seconds'] = time.time()-self.t0
		affpropq['preference_type'] = self.params['preftype']

		### Align Analysis Run object
		analysisq = appionData.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = pathdata
		analysisq['description'] = self.params['description']
		analysisq['alignstack'] = alignstackdata
		analysisq['hidden'] = False
		analysisq['project|projects|project'] = projectid
		### linked through cluster not analysis

		### Clustering Run object
		clusterrunq = appionData.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['description'] = self.params['description']
		clusterrunq['boxsize'] = alignstackdata['boxsize']
		clusterrunq['pixelsize'] = alignstackdata['pixelsize']
		clusterrunq['num_particles'] = self.params['numpart']
		clusterrunq['alignstack'] = alignstackdata
		clusterrunq['project|projects|project'] = projectid
		clusterrunq['analysisrun'] = analysisq
		clusterrunq['affpropparams'] = affpropq

		### Clustering Stack object
		clusterstackq = appionData.ApClusteringStackData()
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
			clusterrefq = appionData.ApClusteringReferenceData()
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
				clusterpartq = appionData.ApClusteringParticlesData()
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
		alignpartq = appionData.ApAlignParticlesData()
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




