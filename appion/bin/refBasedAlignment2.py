#!/usr/bin/env python

#python
import os
import time
import random
import math
import shutil
#appion
import appionScript
import apDisplay
import apFile
import apStack
import apEMAN
import apTemplate
import apParam
import appionData
import apProject
from apSpider import alignment

#=====================
#=====================
class RefBasedAlignScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID --template-list=12,23 --description='test' [ options ]")
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
		self.parser.add_option("--lowpass", dest="lowpass", type="int", default=0,
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning of the particles", metavar="#")
		self.parser.add_option("--highpass", dest="highpass", type="int", default=0,
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--template-list", dest="templatelist",
			help="List of template ids to use, e.g. 1,2", metavar="2,5,6")
		self.parser.add_option("--invert-templates", dest="inverttemplates", default=False,
			action="store_true", help="Invert the density of all the templates")
		self.parser.add_option("-i", "--num-iter", dest="numiter", type="int", default=1,
			help="Number of iterations", metavar="#")
	

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

		boxsize = apStack.getStackBoxsize(self.params['stackid'])
		if self.params['lastring'] > boxsize/2-2:
			apDisplay.printError("last ring radius is too big for boxsize "
				+str(self.params['lastring'])+" > "+str(boxsize/2-2))
		if self.params['lastring']+self.params['xysearch']> boxsize/2-2:
			apDisplay.printError("last ring plus xysearch radius is too big for boxsize "
				+str(self.params['lastring']+self.params['xysearch'])+" > "+str(boxsize/2-2))

		### convert / check template data
		self.templatelist = self.params['templatelist'].strip().split(",")
		if not self.templatelist or type(self.templatelist) != type([]):
			apDisplay.printError("could not parse template list="+self.params['templatelist'])
		self.params['numtemplate'] = len(self.templatelist)
		apDisplay.printMsg("Found "+str(self.params['numtemplate'])+" templates")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])


	#=====================
	def checkDuplicateRefBasedRun(self):
		### setup ref based run
		refrunq = appionData.ApRefBasedRunData()
		refrunq['name'] = self.params['runname']
		refrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = refrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+self.params['runname']+"' and path already exist in database")
		return

	#=====================
	def insertRefBasedRun(self, partlist, alignedstack, imagicstack, insert=False):
		apDisplay.printMsg("committing results to DB")

		### setup alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		### setup ref based run
		refrunq = appionData.ApRefBasedRunData()
		refrunq['runname'] = self.params['runname']
		refrunq['xysearch'] = self.params['xysearch']
		refrunq['xystep'] = self.params['xystep']
		refrunq['first_ring'] = self.params['firstring']
		refrunq['last_ring'] = self.params['lastring']
		refrunq['num_iter'] = self.params['numiter']
		refrunq['invert_templs'] = self.params['inverttemplates']
		refrunq['num_templs'] = self.params['numtemplate']
		#refrunq['csym', int),
		refrunq['run_seconds'] = self.params['runtime']

		### finish alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['refbasedrun'] = refrunq
		alignrunq['hidden'] = False
		alignrunq['bin'] = self.params['bin']
		alignrunq['hp_filt'] = self.params['highpass']
		alignrunq['lp_filt'] = self.params['lowpass']
		alignrunq['runname'] = self.params['runname']
		alignrunq['description'] = self.params['description']
		alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])

		### setup alignment stack
		alignstackq = appionData.ApAlignStackData()
		alignstackq['alignrun'] = alignrunq
		alignstackq['imagicfile'] = imagicstack
		alignstackq['spiderfile'] = alignedstack
		alignstackq['avgmrcfile'] = "average.mrc"
		emancmd = "proc2d templatestack%02d.spi templatestack%02d.hed"%(self.params['numiter'],self.params['numiter'])
		apEMAN.executeEmanCmd(emancmd)
		alignstackq['refstackfile'] = ("templatestack%02d.hed"%(self.params['numiter']))
		alignstackq['alignrun'] = alignrunq
		alignstackq['iteration'] = self.params['numiter']
		alignstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		### check to make sure files exist
		imagicfile = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find stack file: "+imagicfile)
		spiderfile = os.path.join(self.params['rundir'], alignstackq['spiderfile'])
		if not os.path.isfile(spiderfile):
			apDisplay.printError("could not find stack file: "+spiderfile)
		avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
		if not os.path.isfile(avgmrcfile):
			apDisplay.printError("could not find average mrc file: "+avgmrcfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
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
			alignstackq.insert()

		### insert reference data
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
				refq['mrcfile'] = ("templateavg%02d-%02d.mrc"%(iternum,refnum))
				refpath = os.path.abspath(os.path.join(self.params['rundir'], "templates"))
				refq['path'] = appionData.ApPathData(path=refpath)
				refq['alignrun'] = alignrunq
				if insert is True:
					refq.insert()
				if iternum == self.params['numiter']:
					reflist.append(refq)
		#refq['varmrcfile', str),
		#refq['frc_resolution', float),

		### insert particle data
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for partdict in partlist:
			### see apSpider.alignment.alignStack() for more info
			"""
			partdict.keys()
			'num': int(data[0]), #SPIDER NUMBERING: 1,2,3,...
			'template': int(abs(templatenum)), #SPIDER NUMBERING: 1,2,3,...
			'mirror': checkMirror(templatenum),
			'score': float(data[3]),
			'rot': float(data[4]),
			'xshift': float(data[5]),
			'yshift': float(data[6]),
			"""

			alignpartq = appionData.ApAlignParticlesData()
			alignpartq['ref'] = reflist[partdict['template']-1]
			alignpartq['partnum'] = partdict['num']
			alignpartq['alignstack'] = alignstackq
			stackpartdata = apStack.getStackParticle(self.params['stackid'], partdict['num'])
			alignpartq['stackpart'] = stackpartdata
			alignpartq['xshift'] = partdict['xshift']
			alignpartq['yshift'] = partdict['yshift']
			alignpartq['rotation'] = partdict['rot']
			alignpartq['score'] = partdict['score']
			alignpartq['mirror'] = partdict['mirror']

			if insert is True:
				alignpartq.insert()
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

		spiderstack = os.path.join(self.params['rundir'], "start.spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "

		emancmd += "apix="+str(self.stack['apix'])+" "
		if self.params['lowpass'] > 0:
			emancmd += "lp="+str(self.params['lowpass'])+" "
		if self.params['highpass'] > 0:
			emancmd += "hp="+str(self.params['highpass'])+" "
		if self.params['bin'] > 1:
			clipboxsize = int(math.floor(self.stack['boxsize']/self.params['bin'])*self.params['bin'])
			emancmd += "shrink="+str(self.params['bin'])+" "
			emancmd += "clip="+str(clipboxsize)+","+str(clipboxsize)+" "
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

		templatestack = os.path.join(self.params['rundir'], "templatestack00.spi")
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
	def updateTemplateStack(self, alignedstack, partlist, iternum):
		"""
		Function to Average particles that match template to create new templates
		"""

		#templatestr = os.path.join(self.params['rundir'], "templates/filt*.mrc")
		#oldfilelist = glob.glob(templatestr)

		### clear old stacks
		templatestack = os.path.join(self.params['rundir'], ("templatestack%02d.spi" % iternum))
		apFile.removeFile(templatestack, warn=True)

		### calculate correlation stats
		statlist = []
		for partdict in partlist:
			statlist.append(partdict['score'])
		statlist.sort()
		cutoff = statlist[int(0.1*len(partlist))]*0.999
		apDisplay.printMsg("using a 10% correlation cutoff of: "+str(round(cutoff)))

		### init list of files
		keeplists = []
		for templatenum in range(1, self.params['numtemplate']+1):
			f = open(("templates/keeplist%02d-%02d.list" % (iternum, templatenum)), "w")
			keeplists.append(f)
		junk = open(("templates/rejectlist%02d.list" % (iternum)), "w")

		### allocate particles to keep lists
		numjunk = 0
		for partdict in partlist:
			#EMAN lists start at zero
			if partdict['score'] > cutoff:
				keeplists[partdict['template']-1].write(str(partdict['num']-1)+"\n")
			else:
				numjunk+=1
				junk.write(str(partdict['num']-1)+"\n")
		for f in keeplists:
			f.close()
		junk.close()

		### average junk for fun
		apDisplay.printMsg(str(numjunk)+" particles were marked as junk")
		if numjunk == 0:
			junk = open(("templates/rejectlist%02d.list" % (iternum)), "w")
			randpart = random.random()*(len(partlist)-1)
			junk.write(str(randpart)+"\n")
			junk.close()
		junklist = "templates/rejectlist%02d.list" % (iternum)	
		junkmrcfile = "templates/junkavg%02d.mrc" % (iternum)
		emancmd  = ("proc2d "+alignedstack+" "+junkmrcfile
			+" list="+junklist
			+" edgenorm average norm=0,1 ")
		apEMAN.executeEmanCmd(emancmd, showcmd=False)

		### create averaged templates
		filelist = []
		for templatenum in range(1, self.params['numtemplate']+1):
			keeplist = "templates/keeplist%02d-%02d.list" % (iternum, templatenum)	
			mrcfile = "templates/templateavg%02d-%02d.mrc" % (iternum, templatenum)
			if os.path.isfile(keeplist) and os.stat(keeplist)[6] > 1:
				emancmd  = ("proc2d "+alignedstack+" "+mrcfile
					+" list="+keeplist
					+" edgenorm average norm=0,1 ")
				apEMAN.executeEmanCmd(emancmd, showcmd=False)
			else:
				apDisplay.printWarning("No particles aligned to template "+str(templatenum))
				if numjunk == 0:
					apDisplay.printWarning("Using random particle as new template")
				else:
					apDisplay.printWarning("Using worst 10% of particles as new template")
				emancmd  = ("proc2d "+junkmrcfile+" "+mrcfile
					+" addnoise=1.5 "
					+" edgenorm norm=0,1 ")
				apEMAN.executeEmanCmd(emancmd, showcmd=False)
			filelist.append(mrcfile)

		newboxsize = int(math.floor(self.stack['boxsize']/self.params['bin']))
		### create new template stack
		for mrcfile in filelist:
			emancmd  = ("proc2d "+mrcfile+" "+templatestack
				+" clip="+str(newboxsize)+","+str(newboxsize)
				+" edgenorm norm=0,1 spiderswap ")
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

		### test insert to make sure data is not overwritten
		self.params['runtime'] = 0
		#self.checkDuplicateRefBasedRun()

		#convert stack to spider
		spiderstack = self.createSpiderFile()

		#create template stack
		templatestack = self.createTemplateStack()

		#run the alignment
		aligntime = time.time()
		usestack = spiderstack
		oldpartlist = None
		for i in range(self.params['numiter']):
			iternum = i+1
			apDisplay.printColor("\n\nITERATION "+str(iternum), "green")
			alignedstack, partlist = alignment.refBasedAlignParticles(
				usestack, templatestack, spiderstack,
				self.params['xysearch'], self.params['xystep'],
				self.params['numpart'], self.params['numtemplate'],
				self.params['firstring'], self.params['lastring'], 
				iternum=iternum, oldpartlist=oldpartlist)
			oldpartlist = partlist
			usestack = alignedstack
			templatestack = self.updateTemplateStack(alignedstack, partlist, iternum)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		#remove large, worthless stack
		spiderstack = os.path.join(self.params['rundir'], "start.spi")
		apDisplay.printMsg("Removing un-aligned stack: "+spiderstack)
		apFile.removeFile(spiderstack, warn=True)

		#convert aligned stack to imagic
		finalspistack = "aligned.spi"
		shutil.copy(alignedstack, finalspistack)
		imagicstack = "aligned.hed"
		apFile.removeStack(imagicstack)
		emancmd = "proc2d "+finalspistack+" "+imagicstack
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		emancmd = "proc2d "+imagicstack+" average.mrc average"
		apEMAN.executeEmanCmd(emancmd, verbose=True)

		if self.params['commit'] is True:
			apDisplay.printMsg("committing results to DB")
			self.params['runtime'] = aligntime
			self.insertRefBasedRun(partlist, finalspistack, imagicstack, insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")


#=====================
if __name__ == "__main__":
	refBasedAlign = RefBasedAlignScript()
	refBasedAlign.start()
	refBasedAlign.close()

