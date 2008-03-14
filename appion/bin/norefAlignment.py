#!/usr/bin/python -O

import sys
import os
import apDisplay
import apAlignment
import apFile
import appionScript

#=====================
#=====================
class NoRefAlignScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int", default=3000,
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-f", "--first-ring", dest="firstring", type="int", default=2,
			help="First ring radius for correlation (in pixels, > 2)", metavar="#")
		self.parser.add_option("-l", "--last-ring", dest="lastring", type="int",
			help="Last ring radius for correlation (in pixels, < pixel radius)", metavar="#")
		self.parser.add_option("-r", "--rad", "--part-rad", dest="partrad", type="int",
			help="Expected radius of particle for alignment (in Angstroms)", metavar="#")
		self.parser.add_option("-m", "--mask", dest="maskrad", type="float",
			help="Mask radius for particle coran (in Angstroms)", metavar="#")
		self.parser.add_option("--lowpass", dest="lowpass", type="float",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--skip-coran", dest="skipcoran", default=False,
			action="store_true", help="Skip correspondence analysis")

		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of run", metavar="'TEXT'")
		self.parser.add_option("-n", "--runname", dest="runname",
			help="Name for this run", metavar="STR")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))


	#=====================
	def setOutDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		self.params['outdir'] = os.path.join(uppath, "noref", self.params['runname'])

	#=====================
	def preExistingDirectoryError(self):
		apDisplay.printError("Output directory already exists in the database, please change run name")

	#=====================
	def insertNoRefRun(self, insert=False):
		# create a norefParam object
		paramq = appionData.ApNoRefParamsData()
		paramq['num_particles'] = self.params['numpart']
		paramq['particle_diam'] = self.params['diam']
		paramq['mask_diam'] = self.params['maskrad']
		paramq['lp_filt'] = self.params['lowpass']
		paramsdata = appiondb.query(paramq, results=1)

		### create a norefRun object
		runq = appionData.ApNoRefRunData()
		runq['name'] = self.params['runid']
		runq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		runq['stack'] = self.stack['data']
		# ... stackId, runId and norefPath make the norefRun unique:
		uniquerun = appiondb.query(runq, results=1)
		# ... continue filling non-unique variables:
		runq['description'] = self.params['description']

		if paramsdata:
			runq['norefParams'] = paramsdata[0]
		else:
			runq['norefParams'] = paramq
		# ... check if params associated with unique norefRun are consistent:
		if uniquerun and not self.params['classonly']:
			for i in runq:
				if uniquerun[0][i] != runq[i]:
					apDisplay.printError("Run name '"+params['runid']+"' for stackid="+\
						str(params['stackid'])+"\nis already in the database with different parameter: "+str(i))
		#else:
		#	apDisplay.printWarning("Run name '"+params['runid']+"' already exists in database")
		runq['run_seconds'] = self.params['runtime']

		### create a classRun object
		classq = appionData.ApNoRefClassRunData()
		classq['num_classes'] = self.params['numclasses']
		norefrun = appiondb.query(runq, results=1)
		if self.params['classonly']:
			classq['norefRun'] = uniquerun[0]
		elif norefrun:
			classq['norefRun'] = norefrun[0]
		elif not self.params['classonly']:
			classq['norefRun'] = runq
		else:
			apDisplay.printError("parameters have changed for run name '"+self.params['runid']+\
				"', specify 'classonly' to re-average classes")
		# ... numclasses and norefRun make the class unique:
		uniqueclass = appiondb.query(classq, results=1)
		# ... continue filling non-unique variables:
		classq['classFile'] = self.params['classfile']
		classq['varFile'] = self.params['varfile']
		# ... check if params associated with unique classRun are consistent:
		if uniqueclass:
			for i in classq:
				apXml.fancyPrintDict(uniqueclass[0])
				apXml.fancyPrintDict(classq)
				if uniqueclass[0][i] != classq[i]:
					apDisplay.printError("NoRefRun name '"+self.params['runid']+"' for numclasses="+\
						str(self.params['numclasses'])+"\nis already in the database with different parameter: "+str(i))

		classdata = appiondb.query(classq, results=1)

		norefrun = appiondb.query(runq, results=1)
		if not classdata and insert is True:
			# ideal case nothing pre-exists
			apDisplay.printMsg("inserting noref run parameters into database")
			appiondb.insert(classq)

		return

	#=====================
	def createSpiderFile(self):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		emancmd  = "proc2d "
		if not os.path.isfile(self.stack['file']):
			apDisplay.printError("stackfile does not exist: "+self.stack['file'])
		emancmd += self.stack['file']+" "

		spiderstack = os.path.join(self.params['outdir'], "start.spi")
		if os.path.isfile(spiderstack):
			apDisplay.printWarning(outfile+" already exists; removing it")
			time.sleep(5)
			os.remove(spiderstack)
		emancmd += spiderstack+" "
		
		emancmd += "apix="+str(self.stack['apix'])+" "
		if self.params['lowpass'] > 0:
			emancmd += "lp="+str(self.params['lowpass'])+" "
		emancmd += "last="+str(self.params['numpart']-1)+" "
		emancmd += "spiderswap "
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spiderstack

	#=====================
	def averageTemplate(self):
		"""
		takes the spider file and creates an average template of all particles and masks it
		"""
		emancmd  = "proc2d "+self.stack['file']+" template.mrc average"
		apEMAN.executeEmanCmd(emancmd)

		apDisplay.printMsg("Masking average by radius of "+str(self.params['maskrad'])+" Angstroms")
		emancmd  = "proc2d template.mrc template.mrc apix="+str(self.stack['apix'])+" mask="+str(self.params['maskrad'])
		apEMAN.executeEmanCmd(emancmd)

		templatefile = "template.spi"
		if os.path.isfile(templatefile):
			apDisplay.printWarning(templatefile+" already exists; removing it")
			time.sleep(2)
			os.remove(templatefile)
		emancmd  = "proc2d template.mrc "+templatefile+" spiderswap"
		apEMAN.executeEmanCmd(emancmd)

		return templatefile


	#=====================
	def start(self):
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		#convert stack to spider
		spiderstack = self.createSpiderFile()

		#create initialization template
		templatefile = self.averageTemplate()
		#else:
		#	templatefile = self.selectRandomTemplate()

		#run the alignment
		pixrad =  self.params['partrad']/self.stack['apix']
		alignedstack = apSpider.refFreeAlignParticles(
			spiderstack, templatefile, 
			self.params['numpart'], pixrad,
			self.params['firstring'], self.params['lastring'])

		if not self.param['skipcoran']:
			#do coran
			maskpixrad = self.params['maskrad']/self.stack['apix']
			apSpider.correspondenceAnalysis( alignedstack, 
				self.stack['boxsize'], maskpixrad, 
				self.params['numpart'], numfactors=20)

		if self.params['commit'] is True:
			apAlignment.insertNoRefRun(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")


#=====================
if __name__ == "__main__":
	noRefAlign = NoRefAlignScript()
	noRefAlign.start()
	noRefAlign.close()

