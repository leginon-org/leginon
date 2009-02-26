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
import appionData

#=====================
#=====================
class NoRefAlignScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.initmethods = ('allaverage', 'selectrand', 'randpart', 'template')

		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int", default=3000,
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		### radii
		self.parser.add_option("-f", "--first-ring", dest="firstring", type="int", default=2,
			help="First ring radius for correlation (in pixels)", metavar="#")
		self.parser.add_option("-l", "--last-ring", dest="lastring", type="int",
			help="Last ring radius for correlation (in pixels)", metavar="#")
		self.parser.add_option("-r", "--rad", "--part-rad", dest="partrad", type="float",
			help="Expected radius of particle for alignment (in Angstroms)", metavar="#")
		self.parser.add_option("--hp", "--highpass", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--lp", "--lowpass", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

		self.parser.add_option("--init-method", dest="initmethod", default="allaverage",
			help="Initialization method: "+str(self.initmethods), metavar="#")
		self.parser.add_option("--templateid", dest="templateid", type="int",
			help="Template Id for template init method", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['description'] is None:
			apDisplay.printError("run description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		maxparticles = 150000
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: " + str(maxparticles) + " requested: " + str(self.params['numpart']))
		if self.params['initmethod'] not in self.initmethods:
			apDisplay.printError("unknown initialization method defined: "
				+str(self.params['initmethod'])+" not in "+str(self.initmethods))
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
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
	def insertNoRefRun(self, spiderstack, imagicstack, insert=False):
		### setup alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		# create a norefParam object
		norefq = appionData.ApSpiderNoRefRunData()
		norefq['runname'] = self.params['runname']
		norefq['particle_diam'] = 2.0*self.params['partrad']
		norefq['first_ring'] = self.params['firstring']
		norefq['last_ring'] = self.params['lastring']
		norefq['init_method'] = self.params['initmethod']
		norefq['run_seconds'] = self.runtime

		### finish alignment run
		alignrunq['norefrun'] = norefq
		alignrunq['hidden'] = False
		alignrunq['bin'] = self.params['bin']
		alignrunq['hp_filt'] = self.params['highpass']
		alignrunq['lp_filt'] = self.params['lowpass']
		alignrunq['description'] = self.params['description']
		alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])

		# STOP HERE

		### setup alignment stack
		alignstackq = appionData.ApAlignStackData()
		alignstackq['alignrun'] = alignrunq
		alignstackq['imagicfile'] = os.path.basename(imagicstack)
		alignstackq['spiderfile'] = os.path.basename(spiderstack)
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['alignrun'] = alignrunq
		alignstackq['iteration'] = 0
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
			apDisplay.printError("could not find average file: "+avgmrcfile)
		alignstackq['stack'] = self.stack['data']
		alignstackq['boxsize'] = math.floor(self.stack['boxsize']/self.params['bin'])
		alignstackq['pixelsize'] = self.stack['apix']*self.params['bin']
		alignstackq['description'] = self.params['description']
		alignstackq['hidden'] = False
		alignstackq['num_particles'] = self.params['numpart']
		alignstackq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])

		if insert is True:
			alignstackq.insert()

		### create reference
		refq = appionData.ApAlignReferenceData()
		refq['refnum'] = 0
		refq['iteration'] = 0
		refq['mrcfile'] = "template.mrc"
		#refpath = os.path.abspath(os.path.join(self.params['rundir'], "alignment"))
		#refq['path'] = appionData.ApPathData(path=refpath)
		refq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		refq['alignrun'] = alignrunq

		### insert particle data
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for partdict in self.partlist:
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
			alignpartq['ref'] = refq
			alignpartq['partnum'] = partdict['num']
			alignpartq['alignstack'] = alignstackq
			stackpartdata = apStack.getStackParticle(self.params['stackid'], partdict['num'])
			alignpartq['stackpart'] = stackpartdata
			alignpartq['xshift'] = partdict['xshift']
			alignpartq['yshift'] = partdict['yshift']
			alignpartq['rotation'] = partdict['rot']
			#alignpartq['score'] = partdict['score']

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
		emancmd += "last="+str(self.params['numpart']-1)+" "
		emancmd += "shrink="+str(self.params['bin'])+" "
		clipsize = int(math.floor(self.stack['boxsize']/self.params['bin'])*self.params['bin'])
		emancmd += "clip="+str(clipsize)+","+str(clipsize)+" "
		emancmd += "spiderswap edgenorm"
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
	def averageTemplate(self):
		"""
		takes the spider file and creates an average template of all particles
		"""
		emancmd  = "proc2d "+self.stack['file']+" template.mrc average edgenorm"
		apEMAN.executeEmanCmd(emancmd)

		templatefile = self.processTemplate("template.mrc")

		return templatefile

	#=====================
	def selectRandomParticles(self):
		"""
		takes the spider file and creates an average template of all particles
		"""
		### create random keep list
		numrandpart = int(self.params['numpart']/100)+2
		apDisplay.printMsg("Selecting 1% of particles ("+str(numrandpart)+") to average")
		# create random list
		keepdict = {}
		randlist = []
		for i in range(numrandpart):
			rand = int(random.random()*self.params['numpart'])
			while rand in keepdict:
				rand = int(random.random()*self.params['numpart'])
			keepdict[rand] = 1
			randlist.append(rand)
		# sort and write to file
		randlist.sort()
		f = open("randkeep.lst", "w")
		for rand in randlist:
			f.write(str(rand)+"\n")
		f.close()

		emancmd  = "proc2d "+self.stack['file']+" template.mrc list=randkeep.lst average edgenorm"
		apEMAN.executeEmanCmd(emancmd)

		templatefile = self.processTemplate("template.mrc")

		return templatefile

	#=====================
	def pickRandomParticle(self):
		"""
		takes the spider file and creates an average template of all particles
		"""
		### create random keep list
		f = open("randkeep.lst", "w")
		keepdict = {}
		randpart = int(random.random()*self.params['numpart'])
		apDisplay.printMsg("Selecting random particle ("+str(randpart)+") to average")

		emancmd  = ( "proc2d "+self.stack['file']+" template.mrc first="
			+str(randpart)+" last="+str(randpart)+" edgenorm" )
		apEMAN.executeEmanCmd(emancmd)

		templatefile = self.processTemplate("template.mrc")

		return templatefile

	#=====================
	def getTemplate(self):
		"""
		takes the spider file and creates an average template of all particles
		"""
		### create random keep list
		templatedata = apTemplate.getTemplateFromId(self.params['templateid'])
		templatepath = os.path.join(templatedata['path']['path'], templatedata['templatename'])
		if not os.path.isfile(templatepath):
			apDisplay.printError("Could not find template: "+templatepath)
		newpath = os.path.join(self.params['rundir'], "template.mrc")
		shutil.copy(templatepath, newpath)

		### needs to scale template by old apix to new apix

		templatefile = self.processTemplate("template.mrc")

		return templatefile

	#=====================
	def processTemplate(self, mrcfile):
		### shrink
		apDisplay.printMsg("Binning template by a factor of "+str(self.params['bin']))
		clipsize = int(math.floor(self.stack['boxsize']/self.params['bin'])*self.params['bin'])
		emancmd  = ( "proc2d "+mrcfile+" "+mrcfile+" shrink="
			+str(self.params['bin'])+" spiderswap " )
		emancmd += "clip="+str(clipsize)+","+str(clipsize)+" "
		apEMAN.executeEmanCmd(emancmd)

		### normalize and center
		#apDisplay.printMsg("Normalize and centering template")
		#emancmd = "proc2d "+mrcfile+" "+mrcfile+" edgenorm center"
		#apEMAN.executeEmanCmd(emancmd)

		### convert to SPIDER
		apDisplay.printMsg("Converting template to SPIDER")
		templatefile = "template.spi"
		if os.path.isfile(templatefile):
			apFile.removeFile(templatefile, warn=True)
		emancmd = "proc2d template.mrc "+templatefile+" spiderswap "
		apEMAN.executeEmanCmd(emancmd)

		return templatefile	

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

		### create initialization template
		if self.params['initmethod'] == 'allaverage':
			templatefile = self.averageTemplate()
		elif self.params['initmethod'] == 'selectrand':
			templatefile = self.selectRandomParticles()
		elif self.params['initmethod'] == 'randpart':
			templatefile = self.pickRandomParticle()
		elif self.params['initmethod'] == 'template':
			templatefile = self.getTemplate()
		else:
			apDisplay.printError("unknown initialization method defined: "
				+str(self.params['initmethod'])+" not in "+str(self.initmethods))

		apDisplay.printColor("Running spider this can take awhile","cyan")

		### run the alignment
		aligntime = time.time()
		pixrad = int(round(self.params['partrad']/self.stack['apix']/self.params['bin']))
		alignedstack, self.partlist = alignment.refFreeAlignParticles(
			spiderstack, templatefile, 
			self.params['numpart'], pixrad,
			self.params['firstring'], self.params['lastring'],
			rundir = ".")
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### remove large, worthless stack
		spiderstack = os.path.join(self.params['rundir'], "start.spi")
		apDisplay.printMsg("Removing un-aligned stack: "+spiderstack)
		apFile.removeFile(spiderstack, warn=False)

		### convert stack to imagic
		imagicstack = self.convertSpiderStack(alignedstack)

		inserttime = time.time()
		if self.params['commit'] is True:
			self.runtime = aligntime
			self.insertNoRefRun(alignedstack, imagicstack, insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")
		inserttime = time.time() - inserttime

		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))
		apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

#=====================
if __name__ == "__main__":
	noRefAlign = NoRefAlignScript(True)
	noRefAlign.start()
	noRefAlign.close()

