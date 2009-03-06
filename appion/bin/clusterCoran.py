#!/usr/bin/env python

import os
import time
import sys
import re
import appionScript
import apDisplay
import apFile
import apStack
import apEMAN
import apParam
from apSpider import alignment
import appionData


#=====================
#=====================
class ClusterCoranScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --analysisid=ID [ --factor-list=# --num-class=# ]")
		self.parser.add_option("-a",  "--analysisid", dest="analysisid", type="int",
			help="Analysis database id", metavar="ID#")
		self.parser.add_option("-f", "--factor-list", dest="factorstr", type="str", default="1,2,3",
			help="List of factors to use in classification", metavar="#")
		self.parser.add_option("-N", "--num-class-list", dest="numclasslist", type="str", default="4,16,64",
			help="Number of classes to make", metavar="#")
		self.parser.add_option("--method", dest="method", default="hierarch",
			help="Method to use for classification: 'hierarch' or 'kmeans'")

	#=====================
	def checkConflicts(self):
		if self.params['analysisid'] is None:
			apDisplay.printError("analysis id was not defined")
		if self.params['method'] not in ['hierarch','kmeans']:
			apDisplay.printError("--method must be either 'hierarch' or 'kmeans', e.g. --method=hierarch")
		self.analysisdata = appionData.ApAlignAnalysisRunData.direct_query(self.params['analysisid'])

	#=====================
	def setRunDir(self):
		self.params['rundir'] = self.analysisdata['path']['path']

	#=====================
	def readClassDocFile(self, docfile):
		if not os.path.isfile(docfile):
			apDisplay.printError("could not read doc file, "+docfile)
		partlist = []
		f = open(docfile, 'r')
		for line in f:
			if line.strip()[0] == ';':
				continue
			bits = line.split()
			partnum = int(float(bits[2]))
			partlist.append(partnum)
		f.close()
		if not partlist:
			apDisplay.printError("reading class doc file did not work: "+docfile)
		partlist.sort()
		return partlist

	#=====================
	def getAlignParticleData(self, partnum):
		alignpartq = appionData.ApAlignParticlesData()
		alignpartq['alignstack'] = self.analysisdata['alignstack']
		alignpartq['partnum'] = partnum
		alignparts = alignpartq.query(results=1)
		return alignparts[0]

	#=====================
	def insertClusterRun(self, insert=False):
		# Spider Clustering Params
		spiclusterq = appionData.ApSpiderClusteringParamsData()
		spiclusterq['factor_list'] = self.params['factorstr']
		spiclusterq['method'] = self.params['method']

		# create a Clustering Run object
		clusterrunq = appionData.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['description'] = self.params['description']
		clusterrunq['spiderparams'] = spiclusterq
		clusterrunq['boxsize'] = self.analysisdata['alignstack']['boxsize']
		clusterrunq['pixelsize'] = self.analysisdata['alignstack']['pixelsize']
		clusterrunq['num_particles'] = self.analysisdata['alignstack']['num_particles']
		clusterrunq['alignstack'] = self.analysisdata['alignstack']
		clusterrunq['analysisrun'] = self.analysisdata
		clusterrunq['project|projects|project'] = self.analysisdata['project|projects|project']

		apDisplay.printMsg("inserting clustering parameters into database")
		if insert is True:
			clusterrunq.insert()
		self.clusterrun = clusterrunq
		return

	#=====================
	def insertClusterStack(self, classavg=None, classvar=None, numclass=None, insert=False):
		clusterstackq = appionData.ApClusteringStackData()
		clusterstackq['avg_imagicfile'] = classavg+".hed"
		clusterstackq['var_imagicfile'] = classvar+".hed"
		clusterstackq['num_classes'] = numclass
		clusterstackq['clusterrun'] = self.clusterrun
		clusterstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		clusterstackq['hidden'] = False

		imagicfile = os.path.join(self.params['rundir'], clusterstackq['avg_imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find average stack file: "+imagicfile)
		imagicfile = os.path.join(self.params['rundir'], clusterstackq['var_imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find variance stack file: "+imagicfile)

		apDisplay.printMsg("inserting clustering stack into database")
		if insert is True:
			clusterstackq.insert()

		### particle class data
		apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
		for i in range(numclass):
			classnum = i+1
			classdocfile = os.path.join(self.params['rundir'], 
				"cluster/classdoc_%s_%04d.spi" % (self.timestamp, classnum))
			partlist = self.readClassDocFile(classdocfile)
			sys.stderr.write(".")
			for partnum in partlist:
				alignpartdata = self.getAlignParticleData(partnum)
				cpartq = appionData.ApClusteringParticlesData()
				cpartq['clusterstack'] = clusterstackq
				cpartq['alignparticle'] = alignpartdata
				cpartq['partnum'] = partnum
				cpartq['refnum'] = classnum
				cpartq['clusterreference'] = None
				# actual parameters
				if insert is True:
					cpartq.insert()
		return

	#=====================
	def start(self):
		### get original align stack
		alignedstack = os.path.join(self.analysisdata['alignstack']['path']['path'], self.analysisdata['alignstack']['spiderfile'])
		### get database information
		numpart = self.analysisdata['alignstack']['num_particles']
		corandata = os.path.join(self.analysisdata['path']['path'],"coran/corandata")

		### parse factor list
		factorlist = self.params['factorstr'].split(",")
		apDisplay.printMsg("using factorlist "+str(factorlist))
		if len(factorlist) > self.analysisdata['coranrun']['num_factors']:
			apDisplay.printError("Requested factor list is longer than available factors")

		if self.params['commit'] is True:
			self.insertClusterRun(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")

		numclasslist = self.params['numclasslist'].split(",")
		if self.params['method'] != "kmeans":
			rundir = "cluster"
			apParam.createDirectory(rundir)
			### step 1: use coran data to create hierarchy
			dendrogramfile = alignment.hierarchClusterProcess(numpart, factorlist, corandata, rundir, dataext=".spi")
			### step 2: asssign particles to groups based on hierarchy

		for item in  numclasslist:
			t0 = time.time()
			if not item or not re.match("^[0-9]+$", item):
				continue
			numclass = int(item)
			apDisplay.printColor("\n============================\nprocessing class averages for "
				+str(numclass)+" classes\n============================\n", "green")

			#run the classification
			if self.params['method'] == "kmeans":
				apDisplay.printMsg("Using the k-means clustering method")
				classavg,classvar = alignment.kmeansCluster(alignedstack, numpart, numclasses=numclass, 
					timestamp=self.timestamp, factorlist=factorlist, corandata=corandata, dataext=".spi")
			else:
				apDisplay.printMsg("Using the hierarch clustering method")
				classavg,classvar = alignment.hierarchClusterClassify(alignedstack, dendrogramfile, numclass, 
					self.timestamp, rundir, dataext=".spi")
				#classavg,classvar = alignment.hierarchCluster(alignedstack, numpart, numclasses=numclass, 
				#	timestamp=self.timestamp, factorlist=factorlist, corandata=corandata, dataext=".spi")
			if self.params['commit'] is True:
				self.insertClusterStack(classavg, classvar, numclass, insert=True)
			else:
				apDisplay.printWarning("not committing results to DB")

			apDisplay.printMsg("Completed "+str(numclass)+" classes in "+apDisplay.timeString(time.time()-t0))

#=====================
if __name__ == "__main__":
	clusterCoran = ClusterCoranScript(useglobalparams=True)
	clusterCoran.start()
	clusterCoran.close()

