#!/usr/bin/env python
#
import os
import time
import sys
import random
import math
import shutil
#appion
import appionScript
import apDisplay
import apFile
import apTemplate
import apStack
import apEMAN
import apProject
from apSpider import alignment
import spyder
import appionData

#=====================
#=====================
class EdIterAlignScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int", default=3000,
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--numrounds", dest="numrounds", type="int",
			help="Number of AP SR rounds", metavar="#")

		### filters
		self.parser.add_option("--hp", "--highpass", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--lp", "--lowpass", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

		### ed specific parameters
		self.parser.add_option("--ref-template", dest="reftemplate", type="int", 
			help="Template ID to use as alignment reference", metavar="#")
		self.parser.add_option("--template-list", dest="templatelist",
			help="List of template ids to use, e.g. 1,2", metavar="2,5,6")
		self.parser.add_option("-r", "--rad", "--part-rad", dest="partrad", type="float",
			help="Expected radius of particle for alignment (in Angstroms)", metavar="#")
		self.parser.add_option("-i", "--num-iter", dest="refiter", type="int", default=20,
			help="Number of global iterations for ref-based alignment", metavar="#")
		self.parser.add_option("--rfi", "--num-reffree-iter", dest="reffreeiter", type="int", default=3,
			help="Number of iterations for ref-free alignment", metavar="#")
		self.parser.add_option("--invert-templates", dest="inverttemplates", default=False,
			action="store_true", help="Invert the density of all the templates")
		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="Number of processor to use", metavar="ID#")


	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		if self.params['partrad'] is None:
			apDisplay.printError("particle radius was not defined")
		maxparticles = 150000
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: " + str(maxparticles) + " requested: " + str(self.params['numpart']))
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))

		### get num processors
		if self.params['nproc'] is None:
			self.params['nproc'] = apParam.getNumProcessors()

		### convert / check template data
		if self.params['templatelist'] is None:
			apDisplay.printError("template list was not provided")
		self.templatelist = self.params['templatelist'].strip().split(",")
		if not self.templatelist or type(self.templatelist) != type([]):
			apDisplay.printError("could not parse template list="+self.params['templatelist'])
		self.params['numtemplate'] = len(self.templatelist)
		apDisplay.printMsg("Found "+str(self.params['numtemplate'])+" templates")

	#=====================
	def setRunDir(self):
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def checkNoRefRun(self):
		### setup alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

	#=====================
	def insertEdIterRun(self, spiderstack, imagicstack, insert=False):
		return None

	#=====================
	def createSpiderFile(self):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		emancmd  = "proc2d "
		if not os.path.isfile(self.stack['file']):
			apDisplay.printError("stackfile does not exist: "+self.stack['file'])
		emancmd += self.stack['file']+" "

		spiderstack = os.path.join(self.params['rundir'], "start.spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "
		
		emancmd += "apix="+str(self.stack['apix'])+" "
		if self.params['lowpass'] > 0:
			emancmd += "lp="+str(self.params['lowpass'])+" "
		emancmd += "last="+str(self.params['numpart']-1)+" "
		emancmd += "shrink="+str(self.params['bin'])+" "
		clipsize = int(math.floor(self.stack['boxsize']/self.params['bin']/2.0)*self.params['bin']*2.0)
		emancmd += "clip="+str(clipsize)+","+str(clipsize)+" "
		emancmd += "spiderswap"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spiderstack

	#=====================
	def convertSpiderStack(self, spiderstack):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		emancmd  = "proc2d "
		if not os.path.isfile(spiderstack):
			apDisplay.printError("stackfile does not exist: "+spiderstack)
		emancmd += spiderstack+" "

		imagicstack = os.path.join(self.params['rundir'], "alignstack.hed")
		apFile.removeFile(imagicstack, warn=True)
		emancmd += imagicstack+" "

		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return imagicstack

	#=====================
	def createTemplateStack(self):
		"""
		takes the spider file and creates an average template of all particles
		"""

		templatestack = os.path.join(self.params['rundir'], "templatestack.spi")
		apFile.removeFile(templatestack, warn=True)

		### hack to use standard filtering library
		templateparams = {}
		templateparams['apix'] = self.stack['apix']
		templateparams['rundir'] = os.path.join(self.params['rundir'], "templates")
		templateparams['templateIds'] = self.templatelist
		templateparams['bin'] = self.params['bin']
		templateparams['lowpass'] = self.params['lowpass']
		templateparams['median'] = None
		templateparams['pixlimit'] = None
		print templateparams
		apParam.createDirectory(os.path.join(self.params['rundir'], "templates"))
		filelist = apTemplate.getTemplates(templateparams)

		newboxsize = int(math.floor(self.stack['boxsize']/self.params['bin']))
		for mrcfile in filelist:
			emancmd  = ("proc2d templates/"+mrcfile+" "+templatestack
				+" clip="+str(newboxsize)+","+str(newboxsize)
				+" edgenorm spiderswap ")
			if self.params['inverttemplates'] is True:
				emancmd += " invert "
			apEMAN.executeEmanCmd(emancmd, showcmd=False)

		return templatestack

	#=====================
	def setupBatchFile(self, spiderstack, templatestack):
		"""
		sets up Ed's batch script to run
		"""

		### write particle selection file
		partsel = os.path.join(self.params['rundir'], "partlist.spi")
		f = open(partsel, "w")
		for i in range(self.params['numpart']):
			f.write("%06d 1 %06d"%(i+1, i+1))
		f.close()

		refsel = os.path.join(self.params['rundir'], "reflist.spi")
		f = open(refsel, "w")
		for i in range(self.params['numtemplate']):
			f.write("%03d 1 %03d"%(i+1, i+1))
		f.close()

		### read / write batch file
		globalbatch = os.path.join(apParam.getAppionDir(), "spiderbatch/procs/ital.spi")
		localbatch =  os.path.join(self.params['rundir'], "ital.spi")
		gf = open(globalbatch, "r")
		lf = open(localbatch, "w")
		modify = True
		for line in gf:
			if modify is True:
				if re.match("\[pcllist\]", line):
					### sequential list of particle numbers
					lf.write("[pcllist]"+spyder.fileFilter(partsel)+"\n")
				elif re.match("\[pcltmpl\]", line):
					### spider stack of particles
					lf.write("[pcltmpl]"+spyder.fileFilter(spiderstack)+"\n")	
				elif re.match("\[radius\]", line):
					### particle radius in pixels
					pixrad = int(self.params['partrad']/self.stack['apix']/self.stack['bin'])
					lf.write("[radius]%d\n"%(pixrad))
				elif re.match("\[reftmpl\]", line):
					### spider stack of templates
					lf.write("[reftmpl]"+spyder.fileFilter(templatestack)+"\n")
				elif re.match("\[reflist\]", line):
					### sequential list of reference numbers
					lf.write("[reflist]"+spyder.fileFilter(refsel)+"\n")
				elif re.match("\[dir\]", line):
					### sub-directory, we use "."
					lf.write("[dir].\n")
				elif re.match("\[iter\]", line):
					### number of ref-based iterations
					lf.write("[iter]%d\n"%(self.params['refiter']))
				elif re.match("\[apsrtest\]", line):
					### number of ref-free subroutine iterations 
					lf.write("[apsrtest]%d\n"%(self.params['reffreeiter']))
				elif re.match("\[ref\]", line):
					### orientation reference
					templatedata = apTemplate.getTemplateFromId(self.params['reftemplate'])
					templatefile = os.path.join(templatedata['path']['path'], templatedata['templatefile'])
					localtemplate = os.path.join(self.params['rundir'], "orient.spi")
					emancmd "proc2d %s %s spiderswap"%(templatefile, localtemplate)
					apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
					lf.write("[ref]"+spyder.fileFilter(localtemplate)+"\n")
				elif re.match("\[mp\]", line):
					### number of processors
					lf.write("[mp]%d\n"%(self.params['nproc'])
					modify = False
				else:
					lf.write(line)
			else:
				lf.write(line)

	#=====================
	def runSpiderBatch(self)
		### copy over additional batch files
		for bfile in ("a", "b"):
			gfile = os.path.join(apParam.getAppionDir(), "spiderbatch", bfile)
			shutil.copy(


	#=====================
	def start(self):
		self.runtime = 0
		self.partlist = []
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		self.checkNoRefRun()

		### convert stack to spider
		spiderstack = self.createSpiderFile()

		#create template stack
		templatestack = self.createTemplateStack()

		###################################################################
    ### create batch file
		self.setupBatchFile(spiderstack, templatestack)
		### run the spider alignment
		apDisplay.printColor("Running spider this can take awhile","cyan")
    self.runSpiderBatch()
		###################################################################

		### remove large, worthless stack
		apDisplay.printMsg("Removing un-aligned stack: "+spiderstack)
		apFile.removeFile(spiderstack, warn=False)

		### convert stack to imagic
		imagicstack = self.convertSpiderStack(alignedstack)

		inserttime = time.time()
		if self.params['commit'] is True:
			self.runtime = aligntime
			#self.insertNoRefRun(alignedstack, imagicstack, insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")
		inserttime = time.time() - inserttime

		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))
		apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

#=====================
if __name__ == "__main__":
	edIterAlign = EdIterAlignScript(True)
	edIterAlign.start()
	edIterAlign.close()

