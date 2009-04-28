#!/usr/bin/env python
#
import os
import re
import time
import sys
import random
import math
import shutil
#appion
import appionScript
import apDisplay
import apParam
import apFile
import apTemplate
import apStack
import apEMAN
import apProject
from apSpider import alignment
import spyder
import appionData
import cPickle

#=====================
#=====================
class EdIterAlignScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--nparticles", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		### filters
		self.parser.add_option("--hp", "--highpass", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--lp", "--lowpass", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

		### ed specific parameters
		self.parser.add_option("-o", "--orientref", dest="orientref", 
			help="ID of orientation reference", metavar="8")
		self.parser.add_option("-t", "--templates", dest="templatelist",
			help="List of template IDs", metavar="2,5,6")
		self.parser.add_option("--invert-templates", dest="inverttemplates", default=False,
			action="store_true", help="Invert the density of all the templates")
		self.parser.add_option("-r", "--radius", dest="partrad", type="float",
			help="Radius of particle for alignment (in Angstroms)", metavar="#")
		self.parser.add_option("-i", "--iterations", dest="numiter", type="int", default=20,
			help="Number of ref-based classification iterations", metavar="#")
		self.parser.add_option("-f", "--freealigns", dest="freealigns", 
			type="int", default=3, help="Number of ref-free alignment rounds per class", 
			metavar="#")
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
			
		### deal with particles
		maxparticles = 150000
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: "+str(maxparticles)+" requested: "+str(self.params['numpart']))

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

		### convert / check template data
		if self.params['orientref'] is None:
			apDisplay.printError("reference for orientation was not provided")
		self.orientref = self.params['orientref'].strip().split(",")
		if not self.orientref or type(self.orientref) != type([]):
			apDisplay.printError("could not parse orientref="+self.params['orientref'])
		if len(self.orientref) > 1:
			apDisplay.printMsg(str(len(self.orientref))+" orientation references provided. Only first will be used")
		self.orientref = self.orientref[0]

	#=====================
	def setRunDir(self):
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def checkRunNamePath(self):
		### setup alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

	#=====================
	def insertEdIterRun(self, insert=False):
		### setup alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		### setup ed-iter run
		editrunq = appionData.ApEdIterRunData()
		editrunq['runname'] = self.params['runname']
		editrunq['radius'] = self.params['partrad']
		editrunq['num_iter'] = self.params['numiter']
		editrunq['freealigns'] = self.params['freealigns']
		editrunq['invert_templs'] = self.params['inverttemplates']
		editrunq['num_templs'] = self.params['numtemplate']
		#editrunq['csym', int),
		editrunq['run_seconds'] = self.runtime

		### finish alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['editerrun'] = editrunq
		alignrunq['hidden'] = False
		alignrunq['bin'] = self.params['bin']
		alignrunq['hp_filt'] = self.params['highpass']
		alignrunq['lp_filt'] = self.params['lowpass']
		alignrunq['runname'] = self.params['runname']
		alignrunq['description'] = self.params['description']
		alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])

		### setup aligned stack
		alignstackq = appionData.ApAlignStackData()
		alignstackq['alignrun'] = alignrunq
		alignstackq['iteration'] = self.params['numiter']
		alignstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		#final class averages
		avgstack = os.path.join(self.params['rundir'], "avg")
		emancmd = "proc2d "+avgstack+".spi "+avgstack+".hed"
		apEMAN.executeEmanCmd(emancmd)
		alignstackq['refstackfile'] = ("avg.hed")
		#averaged results
		averagedstack = os.path.join(self.params['rundir'], "average.mrc")
		emancmd = "proc2d "+avgstack+".spi "+averagedstack+" average"
		apEMAN.executeEmanCmd(emancmd)
		alignstackq['avgmrcfile'] = "average.mrc"
		#check to be sure files exist
		avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile']) #averaged results
		if not os.path.isfile(avgmrcfile):
			apDisplay.printError("could not find average mrc file: "+avgmrcfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile']) #final averages
		if not os.path.isfile(refstackfile):
			apDisplay.printError("could not find reference stack file: "+refstackfile)
		alignstackq['stack'] = self.stack['data']
		alignstackq['boxsize'] = math.floor(self.stack['boxsize']/self.params['bin'])
		alignstackq['pixelsize'] = self.stack['apix']*self.params['bin']
		alignstackq['description'] = self.params['description']
		alignstackq['hidden'] = False
		alignstackq['num_particles'] = self.params['numpart']
		alignstackq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])

		if insert is True:
			alignstackq.insert() #alignstackq contains alignrunq which contains editrunq

		### setup data from each iteration
		reflist = []
		for j in range(self.params['numiter']):
			iternum = j+1
			for i in range(len(self.templatelist)):
				refnum = i+1
				templateid = self.templatelist[i]
				refq = appionData.ApAlignReferenceData()
				refq['refnum'] = refnum
				refq['iteration'] = iternum
				refq['template'] = apTemplate.getTemplateFromId(templateid)
				refpath = os.path.abspath(os.path.join(self.params['rundir'], "templates"))
				refq['path'] = appionData.ApPathData(path=refpath)
				refq['alignrun'] = alignrunq
				#refq['frc_resolution'] = #(float)
				avgname = os.path.join(self.params['rundir'], "r%02d/avg%03d"%(iternum,refnum) )
				varname = os.path.join(self.params['rundir'], "r%02d/var%03d"%(iternum,refnum) )
				if os.path.isfile(avgname+".spi"):
					emancmd = "proc2d "+avgname+".spi "+avgname+".mrc"
					apEMAN.executeEmanCmd(emancmd)
					refq['mrcfile'] = (avgname+".mrc")
					emancmd = "proc2d "+varname+".spi "+varname+".mrc"
					apEMAN.executeEmanCmd(emancmd)
					refq['varmrcfile'] = (varname+".mrc")
					if insert is True:
						refq.insert()
					if iternum == self.params['numiter']:
						reflist.append(refq)
				else:
					reflist.append(None)

		### insert particle data
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		partlist = self.readApshDocFile("apshdoc.spi","apshdoc.pickle")
		for partdict in partlist:
			alignpartq = appionData.ApAlignParticlesData()
			alignpartq['ref'] = reflist[partdict['template']-1]
			alignpartq['partnum'] = partdict['num']
			alignpartq['alignstack'] = alignstackq
			stackpartdata = apStack.getStackParticle(self.params['stackid'], partdict['num'])
			alignpartq['stackpart'] = stackpartdata
			alignpartq['rotation'] = partdict['rot']
			alignpartq['xshift'] = partdict['xshift']
			alignpartq['yshift'] = partdict['yshift']
			alignpartq['mirror'] = partdict['mirror']
			alignpartq['score'] = partdict['score']

			if insert is True:
				alignpartq.insert() #insert each particle
		return

	#=====================
	def readApshDocFile(self, docfile, picklefile):
		### eventually add this as apSpider.alignment.readAPSHDocFile()
		apDisplay.printMsg("processing alignment doc file "+docfile)
		if not os.path.isfile(docfile):
			apDisplay.printError("Doc file, "+docfile+" does not exist")
		docf = open(docfile, "r")
		partlist = []
		for line in docf:
			data = line.strip().split()
			if data[0] == ";":
				continue
			if len(data) < 15:
				continue
			"""
			2 psi,
			3 theta,
			4 phi,
			5 refNum,
			6 particleNum,
			7 sumRotation,
			8 sumXshift,
			9 sumYshift,
			10 #refs,
			11 anglechange,
			12 cross-correlation,
			13 currentRotation,
			14 currentXshift,
			15 currentYshift,
			16 currentMirror
			"""
			partdict = {
				'psi': float(data[2]),
				'theta': float(data[3]),
				'phi': float(data[4]),
				'template': int(abs( float(data[5]) )),
				'num': int(float(data[6])),
				'rot': alignment.wrap360(float(data[7])),
				'xshift': float(data[8]),
				'yshift': float(data[9]),
				'mirror': alignment.checkMirror( float(data[16]) ),
				'score': float(data[12]),
				}
		partlist.append(partdict)
		docf.close()
		picklef = open(picklefile, "w")
		cPickle.dump(partlist, picklef)
		picklef.close()
		return partlist
		
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
		emancmd += "clip="+str(self.clipsize)+","+str(self.clipsize)+" "
		emancmd += "spiderswap"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spiderstack

	#=====================
	def convertSpiderStack(self, spiderstack):
		"""
		converts spider stack to imagicstack
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
		convert spider template stack
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
		print 'Converting reference templates:\n', templateparams
		apParam.createDirectory(os.path.join(self.params['rundir'], "templates"))
		filelist = apTemplate.getTemplates(templateparams)

		for mrcfile in filelist:
			emancmd  = ("proc2d templates/"+mrcfile+" "+templatestack
				+" clip="+str(self.clipsize)+","+str(self.clipsize)
				+" edgenorm spiderswap ")
			if self.params['inverttemplates'] is True:
				emancmd += " invert "
			apEMAN.executeEmanCmd(emancmd, showcmd=False)

		return templatestack

	#=====================
	def createOrientationReference(self):
		"""
		convert spider orientation reference
		"""

		orientref = os.path.join(self.params['rundir'], "orient.spi")
		apFile.removeFile(orientref, warn=True)

		#templatedata = apTemplate.getTemplateFromId(self.params['orientref'])
		#templatefile = os.path.join(templatedata['path']['path'], templatedata['templatename'])

		### hack to use standard filtering library
		templateparams = {}
		templateparams['apix'] = self.stack['apix']
		templateparams['rundir'] = os.path.join(self.params['rundir'], "templates")
		templateparams['templateIds'] = [self.orientref,]
		templateparams['bin'] = self.params['bin']
		templateparams['lowpass'] = self.params['lowpass']
		templateparams['median'] = None
		templateparams['pixlimit'] = None
		print 'Converting orientation reference:\n', templateparams
		apParam.createDirectory(os.path.join(self.params['rundir'], "templates"))
		filelist = apTemplate.getTemplates(templateparams)

		for mrcfile in filelist:
			emancmd  = ("proc2d templates/"+mrcfile+" "+orientref
				+" clip="+str(self.clipsize)+","+str(self.clipsize)
				+" edgenorm spiderswap-single ")
			if self.params['inverttemplates'] is True:
				emancmd += " invert "
			apEMAN.executeEmanCmd(emancmd, showcmd=False)

		return orientref
		
	#=====================
	def setupBatchFile(self, spiderstack, templatestack, orientref):
		"""
		sets up Ed's batch script to run
		"""

		### write particle selection file
		partsel = os.path.join(self.params['rundir'], "partlist.spi")
		f = open(partsel, "w")
		for i in range(self.params['numpart']):
			f.write("%06d 1 %06d \n"%(i+1, i+1))
		f.close()

		refsel = os.path.join(self.params['rundir'], "reflist.spi")
		f = open(refsel, "w")
		for i in range(self.params['numtemplate']):
			f.write("%03d 1 %03d \n"%(i+1, i+1))
		f.close()

		### read / write batch file
		globalbatch = os.path.join(apParam.getAppionDirectory(), "spiderbatch/procs/ital.spi")
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
					lf.write("[pcltmpl]"+spyder.fileFilter(spiderstack)+"@****** \n")	
				elif re.match("\[radius\]", line):
					### particle radius in pixels
					pixrad = int(self.params['partrad']/self.stack['apix']/self.params['bin'])
					lf.write("[radius]%d\n"%(pixrad))
				elif re.match("\[reftmpl\]", line):
					### spider stack of templates
					lf.write("[reftmpl]"+spyder.fileFilter(templatestack)+"@*** \n")
				elif re.match("\[reflist\]", line):
					### sequential list of reference numbers
					lf.write("[reflist]"+spyder.fileFilter(refsel)+"\n")
				elif re.match("\[dir\]", line):
					### sub-directory, we use "."
					lf.write("[dir].\n")
				elif re.match("\[iter\]", line):
					### number of ref-based iterations
					lf.write("[iter]%d\n"%(self.params['numiter']))
				elif re.match("\[apsrtest\]", line):
					### number of ref-free subroutine iterations 
					lf.write("[apsrtest]%d\n"%(self.params['freealigns']))
				elif re.match("\[ref\]", line):
					### orientation reference
					lf.write("[ref]"+spyder.fileFilter(orientref)+"\n")
				elif re.match("\[mp\]", line):
					### number of processors
					lf.write("[mp]%d\n"%(self.params['nproc']))
					modify = False
				else:
					lf.write(line)
			else:
				lf.write(line)

	#=====================
	def runSpiderBatch(self):
		### set SPPROC_DIR environment variable
		spiprocdir = os.path.join(apParam.getAppionDirectory(), "spiderbatch/")
		mySpider = spyder.SpiderSession(logo=True, spiderprocdir=spiprocdir, projext=".spi")
		mySpider.toSpider("@ital")
		mySpider.close()


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
		self.clipsize = int(math.floor(self.stack['boxsize']/self.params['bin']/2.0)*self.params['bin']*2.0)

		#self.checkRunNamePath()

		### convert stack to spider
		spiderstack = self.createSpiderFile()

		#create template stack
		templatestack = self.createTemplateStack()
		
		#create orientation reference
		orientref = self.createOrientationReference()

		###################################################################
		aligntime = time.time()
		### create batch file
		self.setupBatchFile(spiderstack, templatestack, orientref)
		### run the spider alignment
		apDisplay.printColor("Running iterative ref-classification and free-alignment with spider","cyan")
		self.runSpiderBatch()
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))
		###################################################################

		### remove unaligned spider stack
		apDisplay.printMsg("Removing un-aligned stack: "+spiderstack)
		apFile.removeFile(spiderstack, warn=False)

		###output is class averages, variances, paricle lists and alignment parameters
		###imagicstack = self.convertSpiderStack(alignedstack) ###there is not aligned stack

		#check to be sure files exist
		avgfile = os.path.join(self.params['rundir'], "avg.spi") #class averages
		if not os.path.isfile(avgfile):
			apDisplay.printError("could not find average stack file: "+avgfile)

		inserttime = time.time()
		if self.params['commit'] is True:
			apDisplay.printWarning("committing results to DB")
			self.runtime = aligntime
			self.insertEdIterRun(insert=True)
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

