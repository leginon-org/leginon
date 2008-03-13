#!/usr/bin/python -O

import sys
import os
import apDisplay
import apParam
import apAlignment
import appionScript

#=====================
#=====================
class UploadModelScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-n", "--num-part", dest="numpart", type="int", default=3000,
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-f", "--first-ring", dest="firstring", type="int", default=2,
			help="First ring radius for correlation (in pixels, > 2)", metavar="#")
		self.parser.add_option("-l", "--last-ring", dest="lastring", type="int",
			help="Last ring radius for correlation (in pixels, < pixel radius)", metavar="#")
		self.parser.add_option("-r", "--rad", dest="pixrad", type="int",
			help="Expected pixel radius of particle for align", metavar="#")
		self.parser.add_option("-m", "--mask", dest="maskrad", type="int",
			help="Mask radius for particle coran (in pixels)", metavar="#")
		self.parser.add_option("--lowpass", dest="pixrad", type="float",
			help="Low pass filter radius (in pixels, > 2)", metavar="#")

		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of run", metavar="'TEXT'")
		self.parser.add_option("--runname", dest="runname",
			help="Name for this run", metavar="STR")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")

	#=====================
	def setOutDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		self.params['outdir'] = os.path.join(uppath, "noref", self.params['runname'])

	#=====================
	def insertNoRefRun(self, insert=False):
		# create a norefParam object
		paramq = appionData.ApNoRefParamsData()
		paramq['num_particles'] = self.params['numparticles']
		paramq['particle_diam'] = self.params['diam']
		paramq['mask_diam'] = self.params['mask']
		paramq['lp_filt'] = self.params['imask']
		paramsdata = appiondb.query(paramq, results=1)

		### create a norefRun object
		runq = appionData.ApNoRefRunData()
		runq['name'] = self.params['runid']
		runq['path'] = appionData.ApPathData(path=os.path.abspath(params['outdir']))
		runq['stack'] = appiondb.direct_query(appionData.ApStackData, self.params['stackid'])
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
			apDisplay.printError("parameters have changed for run name '"+params['runid']+\
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
					apDisplay.printError("NoRefRun name '"+params['runid']+"' for numclasses="+\
						str(params['numclasses'])+"\nis already in the database with different parameter: "+str(i))

		classdata = appiondb.query(classq, results=1)

		norefrun = appiondb.query(runq, results=1)
		if not classdata and insert is True:
			# ideal case nothing pre-exists
			apDisplay.printMsg("inserting noref run parameters into database")
			appiondb.insert(classq)

		return


	#=====================
	def start(self):
		apAlignment.getStackInfo(params)
		if self.params['commit']is True:
			apAlignment.insertNoRefRun(params, insert=False)
		else:
			apDisplay.printWarning("not committing results to DB")

		classfile = os.path.join(params['rundir'], "classes_avg.spi")
		varfile = os.path.join(params['rundir'], "classes_var.spi")
		if not os.path.isfile(classfile):
			apAlignment.createSpiderFile(params)
			apAlignment.averageTemplate(params)
			apAlignment.createNoRefSpiderBatchFile(params)
			apAlignment.runSpiderClass(params)
		else:
			apDisplay.printWarning("particles were already aligned for this runid, only redoing clustering") 
			apAlignment.createNoRefSpiderBatchFile(params)
			apAlignment.runSpiderClass(params, reclass=True)

		classfile = os.path.join(params['rundir'],params['classfile']+".spi")
		if not os.path.isfile(classfile):
			apDisplay.printError("failed to write classfile, "+classfile)

		apAlignment.convertClassfileToImagic(params)

		classfile = os.path.join(params['rundir'],params['classfile']+".hed")
		if self.params['commit']is True:
			apAlignment.insertNoRefRun(params, insert=True)
		if self.params['numclasses'] <= 80:
			apAlignment.classHistogram(params)
		apDisplay.printMsg("SUCCESS: classfile located at:\n"+classfile)
