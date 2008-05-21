#!/usr/bin/python -O

#python
import os
import time
#appion
import apDisplay
import apAlignment
import apFile
import apStack
import apEMAN
import apTemplate
import apParam
from apSpider import alignment
import appionScript

#=====================
#=====================
class RefBasedAlignScript(appionScript.AppionScript):

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
		self.parser.add_option("-x", "--xy-search", dest="xysearch", type="int", default=3,
			help="XY search distance (in pixels)", metavar="#")
		self.parser.add_option("--xy-step", dest="xystep", type="int", default=1,
			help="XY step distance (in pixels)", metavar="#")
		self.parser.add_option("--lowpass", dest="lowpass", type="float",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--template-list", dest="templatelist",
			help="List of template id to use", metavar="x,y,z")
		self.parser.add_option("--invert-templates", dest="inverttemplates", default=False,
			action="store_true", help="Invert the density of the templates")
		self.parser.add_option("-i", "--num-iter", dest="numiter", type="int", default=1,
			help="Number of iterations", metavar="#")

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
		if self.params['templatelist'] is None:
			apDisplay.printError("template list was not provided")
		if self.params['lastring'] is None:
			apDisplay.printError("a last ring radius was not provided")
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
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['outdir'] = os.path.join(uppath, "refbased", self.params['runname'])

	#=====================
	def insertRefBasedRun(self, insert=False):
		# create a refBasedParam object
		paramq = appionData.ApRefBasedParamsData()
		paramq['num_particles'] = self.params['numpart']
		paramq['particle_diam'] = self.params['diam']
		paramq['lp_filt'] = self.params['lowpass']
		paramsdata = appiondb.query(paramq, results=1)

		### create a refBasedRun object
		runq = appionData.ApRefBasedRunData()
		runq['name'] = self.params['runid']
		runq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		runq['stack'] = self.stack['data']
		# ... stackId, runId and refBasedPath make the refBasedRun unique:
		uniquerun = appiondb.query(runq, results=1)
		# ... continue filling non-unique variables:
		runq['description'] = self.params['description']

		if paramsdata:
			runq['refBasedParams'] = paramsdata[0]
		else:
			runq['refBasedParams'] = paramq
		# ... check if params associated with unique refBasedRun are consistent:
		if uniquerun and not self.params['classonly']:
			for i in runq:
				if uniquerun[0][i] != runq[i]:
					apDisplay.printError("Run name '"+params['runid']+"' for stackid="+\
						str(params['stackid'])+"\nis already in the database with different parameter: "+str(i))
		#else:
		#	apDisplay.printWarning("Run name '"+params['runid']+"' already exists in database")
		runq['run_seconds'] = self.params['runtime']

		### create a classRun object
		classq = appionData.ApRefBasedClassRunData()
		classq['num_classes'] = self.params['numclasses']
		refBasedrun = appiondb.query(runq, results=1)
		if self.params['classonly']:
			classq['refBasedRun'] = uniquerun[0]
		elif refBasedrun:
			classq['refBasedRun'] = refBasedrun[0]
		elif not self.params['classonly']:
			classq['refBasedRun'] = runq
		else:
			apDisplay.printError("parameters have changed for run name '"+self.params['runid']+\
				"', specify 'classonly' to re-average classes")
		# ... numclasses and refBasedRun make the class unique:
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
					apDisplay.printError("RefBasedRun name '"+self.params['runid']+"' for numclasses="+\
						str(self.params['numclasses'])+"\nis already in the database with different parameter: "+str(i))

		classdata = appiondb.query(classq, results=1)

		refBasedrun = appiondb.query(runq, results=1)
		if not classdata and insert is True:
			# ideal case nothing pre-exists
			apDisplay.printMsg("inserting refBased run parameters into database")
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
			apDisplay.printWarning(spiderstack+" already exists; removing it")
			time.sleep(5)
			os.remove(spiderstack)
		emancmd += spiderstack+" "
		
		emancmd += "apix="+str(self.stack['apix'])+" "
		if self.params['lowpass'] > 0:
			emancmd += "lp="+str(self.params['lowpass'])+" "
		emancmd += "last="+str(self.params['numpart']-1)+" "
		emancmd += "spiderswap edgenorm"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spiderstack

	#=====================
	def createTemplateStack(self):
		"""
		takes the spider file and creates an average template of all particles
		"""
		templatelist = self.params['templatelist'].strip().split(",")
		if not templatelist or type(templatelist) != type([]):
			apDisplay.printError("could not parse template list="+self.params['templatelist'])
		self.params['numtemplate'] = len(templatelist)

		templatestack = os.path.join(self.params['outdir'], "templatestack00.spi")
		if os.path.isfile(templatestack):
			apDisplay.printWarning(templatestack+" already exists; removing it")
			time.sleep(2)
			os.remove(templatestack)

		templateparams = {}
		templateparams['apix'] = self.stack['apix']
		templateparams['rundir'] = os.path.join(self.params['outdir'], "templates")
		templateparams['templateIds'] = templatelist
		templateparams['bin'] = 1
		templateparams['lowpass'] = self.params['lowpass']
		templateparams['median'] = None
		templateparams['pixlimit'] = None
		apParam.createDirectory(os.path.join(self.params['outdir'], "templates"))
		filelist = apTemplate.getTemplates(templateparams)

		for mrcfile in filelist:
			emancmd  = ("proc2d templates/"+mrcfile+" "+templatestack
				+" clip="+str(self.stack['boxsize'])+","+str(self.stack['boxsize'])
				+" edgenorm spiderswap ")
			if self.params['inverttemplates'] is True:
				emancmd += " invert "
			apEMAN.executeEmanCmd(emancmd, showcmd=False)

		return templatestack

	#=====================
	def updateTemplateStack(self, alignedstack, partlist, iternum):
		#templatestr = os.path.join(self.params['outdir'], "templates/filt*.mrc")
		#oldfilelist = glob.glob(templatestr)

		### clear old stacks
		templatestack = os.path.join(self.params['outdir'], ("templatestack%02d.spi" % iternum))
		if os.path.isfile(templatestack):
			apDisplay.printWarning(templatestack+" already exists; removing it")
			time.sleep(2)
			os.remove(templatestack)

		### calculate correlation stats
		statlist = []
		for partdict in partlist:
			statlist.append(partdict['score'])
		statlist.sort()
		cutoff = statlist[int(0.1*len(partlist))]
		apDisplay.printMsg("using a 10% correlation cutoff of: "+str(round(cutoff)))

		### init list of files
		keeplists = []
		for templatenum in range(1, self.params['numtemplate']+1):
			f = open(("templates/keeplist%02d-%02d.list" % (iternum, templatenum)), "w")
			keeplists.append(f)
		junk = open(("templates/rejectlist%02d.list" % (iternum)), "w")

		### allocate particles to keep lists
		for partdict in partlist:
			#EMAN lists start at zero
			if partdict['score'] > cutoff:
				keeplists[partdict['template']-1].write(str(partdict['num']-1)+"\n")
			else:
				junk.write(str(partdict['num']-1)+"\n")
		for f in keeplists:
			f.close()
		junk.close()

		### average junk for fun
		junklist = "templates/rejectlist%02d.list" % (iternum)	
		junkmrcfile = "templates/junkavg%02d.mrc" % (iternum)
		emancmd  = ("proc2d "+alignedstack+" "+junkmrcfile
			+" list="+junklist
			+" edgenorm average ")
		apEMAN.executeEmanCmd(emancmd, showcmd=False)

		### create averaged templates
		filelist = []
		for templatenum in range(1, self.params['numtemplate']+1):
			keeplist = "templates/keeplist%02d-%02d.list" % (iternum, templatenum)	
			mrcfile = "templates/templateavg%02d-%02d.mrc" % (iternum, templatenum)
			if os.path.isfile(keeplist) and os.stat(keeplist)[6] > 1:
				emancmd  = ("proc2d "+alignedstack+" "+mrcfile
					+" list="+keeplist
					+" edgenorm average ")
				apEMAN.executeEmanCmd(emancmd, showcmd=False)
			else:
				apDisplay.printWarning("No particles aligned to template "+str(templatenum))
				emancmd  = ("proc2d "+junkmrcfile+" "+mrcfile
					+" addnoise=0.1 "
					+" edgenorm ")
				apEMAN.executeEmanCmd(emancmd, showcmd=False)
			filelist.append(mrcfile)

		### create new template stack
		for mrcfile in filelist:
			emancmd  = ("proc2d "+mrcfile+" "+templatestack
				+" clip="+str(self.stack['boxsize'])+","+str(self.stack['boxsize'])
				+" edgenorm spiderswap ")
			apEMAN.executeEmanCmd(emancmd, showcmd=False)

		return templatestack

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

		#create template stack
		templatestack = self.createTemplateStack()

		#run the alignment
		aligntime = time.time()
		usestack = spiderstack
		for i in range(self.params['numiter']):
			iternum = i+1
			apDisplay.printColor("\n\nITERATION "+str(iternum), "green")
			alignedstack, partlist = alignment.refBasedAlignParticles(
				usestack, templatestack, 
				self.params['xysearch'], self.params['xystep'],
				self.params['numpart'], self.params['numtemplate'],
				self.params['firstring'], self.params['lastring'], iternum=iternum)
			usestack = alignedstack
			templatestack = self.updateTemplateStack(alignedstack, partlist, iternum)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		#remove large, worthless stack
		spiderstack = os.path.join(self.params['outdir'], "start.spi")
		apDisplay.printMsg("Removing un-aligned stack: "+spiderstack)
		os.remove(spiderstack)

		if self.params['commit'] is True:
			apDisplay.printError("not working yet")
			apAlignment.insertRefBasedRun(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")

		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))


#=====================
if __name__ == "__main__":
	refBasedAlign = RefBasedAlignScript()
	refBasedAlign.start()
	refBasedAlign.close()

