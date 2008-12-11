#!/usr/bin/env python

import os
import time
import sys
import appionScript
import apDisplay
import apAlignment
import apFile
import apStack
import apEMAN
from apSpider import alignment
import appionData


#=====================
#=====================
class NoRefClassScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --noref=ID [ --num-part=# ]")

		#required
		self.parser.add_option("-i",  "--norefid", dest="norefid", type="int",
			help="No ref database id", metavar="ID#")

		#with defaults
		self.parser.add_option("-f", "--factor-list", dest="factorstr", type="str", default="1,2,3",
			help="List of factors to use in classification", metavar="#")
		self.parser.add_option("-N", "--num-class", dest="numclass", type="int", default=40,
			help="Number of classes to make", metavar="#")
		self.parser.add_option("--method", dest="method", default="hierarch",
			help="Method to use for classification: 'hierarch' or 'kmeans'")

	#=====================
	def checkConflicts(self):
		if self.params['norefid'] is None:
			apDisplay.printError("No ref id was not defined, use --norefid=#")
		if self.params['numclass'] > 900:
			apDisplay.printError("too many classes defined: "+str(self.params['numclass']))
		if self.params['method'] not in ['hierarch','kmeans']:
			apDisplay.printError("--method must be either 'hierarch' or 'kmeans', e.g. --method=hierarch")
		self.norefdata = appionData.ApNoRefRunData.direct_query(self.params['norefid'])
		if self.norefdata is None:
			apDisplay.printError("noref id '"+str(self.params['norefid'])+"' was not found")

	#=====================
	def setRunDir(self):
		self.params['rundir'] = self.norefdata['path']['path']

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
		if not partlist:
			apDisplay.printError("reading class doc file did not work: "+docfile)
		partlist.sort()
		return partlist

	#=====================
	def getNoRefPart(self, partnum):
		norefpartq = appionData.ApNoRefAlignParticlesData()
		norefpartq['norefRun'] = self.norefdata
		stackid = self.norefdata['stack'].dbid
		stackpart = apStack.getStackParticle(stackid, partnum)
		norefpartq['particle'] = stackpart
		norefparts = norefpartq.query(results=1)

		return norefparts[0]

	#=====================
	def insertNoRefClass(self, classavg=None, classvar=None, insert=False):
		# create a norefParam object
		classq = appionData.ApNoRefClassRunData()
		classq['num_classes'] = self.params['numclass']
		classq['norefRun'] = self.norefdata
		uniqueclass = classq.query(results=1)
		if uniqueclass:
			apDisplay.printWarning("Classification of "+str(classq['num_classes'])+" classes for norefid="+\
				str(self.params['norefid'])+"\nis already in the database")

		classq['factor_list'] = self.params['factorstr']
		if classavg is None:
			classq['classFile'] = ("cluster/classavgstack%03d_%s" % (self.params['numclass'], self.timestamp))
		else:
			classq['classFile'] = classavg
		if classvar is None:
			classq['varFile'] = ("cluster/classvarstack%03d_%s" % (self.params['numclass'], self.timestamp))
		else:
			classq['varFile'] = classvar

		classq['method'] = self.params['method']

		apDisplay.printMsg("inserting classification parameters into database")
		if insert is True:
			classq.insert()

		### particle class data
		apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
		for i in range(self.params['numclass']):
			classnum = i+1
			classdocfile = os.path.join(self.params['rundir'], "cluster/classdoc%04d.spi" % (classnum))
			partlist = self.readClassDocFile(classdocfile)
			sys.stderr.write(".")
			for partnum in partlist:
				norefpart = self.getNoRefPart(partnum)
				cpartq = appionData.ApNoRefClassParticlesData()
				cpartq['classRun'] = classq
				cpartq['noref_particle'] = norefpart
				cpartq['classNumber'] = classnum
				# actual parameters
				if insert is True:
					cpartq.insert()

		return

	#=====================
	def start(self):

		alignedstack = os.path.join(self.norefdata['path']['path'], "alignedstack")
		numpart = self.norefdata['norefParams']['num_particles']
		factorlist = self.params['factorstr'].split(",")
		apDisplay.printMsg("using factorlist "+str(factorlist))
		if len(factorlist) > self.norefdata['norefParams']['num_factors']:
			apDisplay.printError("Requested factor list is longer than available factors")

		#run the classification
		if self.params['method'] == "kmeans":
			apDisplay.printMsg("Using the k-means clustering method")
			classavg,classvar = alignment.kmeansCluster(alignedstack, numpart, numclasses=self.params['numclass'], 
				timestamp=self.timestamp, factorlist=factorlist, corandata="coran/corandata", dataext=".spi")
		else:
			apDisplay.printMsg("Using the hierarch clustering method")
			classavg,classvar = alignment.hierarchCluster(alignedstack, numpart, numclasses=self.params['numclass'], 
				timestamp=self.timestamp, factorlist=factorlist, corandata="coran/corandata", dataext=".spi")


		if self.params['commit'] is True:
			self.insertNoRefClass(classavg, classvar, insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")

#=====================
if __name__ == "__main__":
	noRefClass = NoRefClassScript(True)
	noRefClass.start()
	noRefClass.close()

