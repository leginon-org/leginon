#!/usr/bin/python -O

import os
import time
import sys
import apDisplay
import apAlignment
import apFile
import apStack
import apEMAN
from apSpider import alignment
import appionScript
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
		self.parser.add_option("-f", "--factor-list", dest="factorlist", type="str", default="1-3",
			help="List of factors to use in classification", metavar="#")
		self.parser.add_option("-N", "--num-class", dest="numclass", type="int", default=40,
			help="Number of classes to make", metavar="#")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit noref class to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit noref class to database")
		#self.parser.add_option("-o", "--outdir", dest="outdir",
		#	help="Output directory", metavar="PATH")

	#=====================
	def checkConflicts(self):
		if self.params['norefid'] is None:
			apDisplay.printError("No ref id was not defined")
		if self.params['numclass'] > 200:
			apDisplay.printError("too many classes defined: "+str(self.params['numclass']))
		self.norefdata = self.appiondb.direct_query(appionData.ApNoRefRunData, self.params['norefid'])

	#=====================
	def setOutDir(self):
		self.params['outdir'] = self.norefdata['path']['path']

	#=====================
	def insertNoRefClassRun(self, insert=False):
		# create a norefParam object
		classq = appionData.ApNoRefClassRunData()
		classq['num_classes'] = self.params['numclass']
		classq['norefRun'] = self.norefdata
		uniqueclass = classq.query(results=1)
		if uniqueclass:
			apDisplay.printWarning("Classification of "+str(classq['num_classes'])+" classes for norefid="+\
				str(self.params['norefid'])+"\nis already in the database")

		classq['factor_list'] = self.params['factorlist']
		classq['classFile'] = ("classavgimg%03d.hed" % self.params['numclass'])
		classq['varFile'] = ("classvarimg%03d.hed" % self.params['numclass'])

		apDisplay.printMsg("inserting classification parameters into database")
		if insert is True:
			classq.insert()
		"""
		### particle class data
		apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
		count = 0
		for partdict in self.partlist:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")
			partq = appionData.ApNoRefAlignParticlesData()
			partq['norefRun'] = runq
			# I can only assume this gets the correct particle:
			stackpart = apStack.getStackParticle(self.params['stackid'], partdict['num'])
			partq['particle'] = stackpart
			# actual parameters
			partq['shift_x'] = partdict['xshift']		
			partq['shift_y'] = partdict['yshift']		
			partq['rotation'] = partdict['rot']
			if insert is True:
				partq.insert()
		"""
		return

	#=====================
	def start(self):

		alignedstack = os.path.join(self.norefdata['path']['path'], "alignedstack.spi")
		numpart = self.norefdata['num_particles']

		#run the classification
		alignment.hierarchCluster(alignedstack, numpart, numclasses=self.params['numclass'], 
			factorlist=self.params['factorlist'], corandata="coran/corandata", dataext=".spi")

		if self.params['commit'] is True:
			self.insertNoRefClass(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")

#=====================
if __name__ == "__main__":
	noRefClass = NoRefClassScript()
	noRefClass.start()
	noRefClass.close()

