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
import apAlignment
import apFile
import apTemplate
import apStack
import apEMAN
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
		self.parser.add_option("--num-factors", dest="numfactors", type="int", default=8,
			help="Number of factors to use in classification", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		### radii
		self.parser.add_option("-f", "--first-ring", dest="firstring", type="int", default=2,
			help="First ring radius for correlation (in pixels)", metavar="#")
		self.parser.add_option("-l", "--last-ring", dest="lastring", type="int",
			help="Last ring radius for correlation (in pixels)", metavar="#")
		self.parser.add_option("-r", "--rad", "--part-rad", dest="partrad", type="float",
			help="Expected radius of particle for alignment (in Angstroms)", metavar="#")
		self.parser.add_option("-m", "--mask", dest="maskrad", type="float",
			help="Mask radius for particle coran (in Angstoms)", metavar="#")
		self.parser.add_option("--lowpass", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

		self.parser.add_option("--skip-coran", dest="skipcoran", default=False,
			action="store_true", help="Skip correspondence analysis")
		self.parser.add_option("--init-method", dest="initmethod", default="allaverage",
			help="Initialization method: "+str(self.initmethods), metavar="#")
		self.parser.add_option("--templateid", dest="templateid", type="int",
			help="Template Id for template init method", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['maskrad'] is None:
			apDisplay.printError("a mask radius was not provided")
		maxparticles = 150000
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: " + str(maxparticles) + " requested: " + str(self.params['numpart']))
		if self.params['initmethod'] not in self.initmethods:
			apDisplay.printError("unknown initialization method defined: "
				+str(self.params['initmethod'])+" not in "+str(self.initmethods))
		if self.params['numfactors'] > 20:
			apDisplay.printError("too many factors defined: "+str(self.params['numfactors']))
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
		self.params['rundir'] = os.path.join(uppath, "noref", self.params['runname'])

	#=====================
	def insertNoRefRun(self, insert=False):
		# create a norefParam object
		paramq = appionData.ApNoRefParamsData()
		paramq['num_particles'] = self.params['numpart']
		paramq['num_factors'] = self.params['numfactors']
		paramq['particle_diam'] = 2.0*self.params['partrad']
		paramq['mask_diam'] = 2.0*self.params['maskrad']
		paramq['lp_filt'] = self.params['lowpass']
		paramq['first_ring'] = self.params['firstring']
		paramq['last_ring'] = self.params['lastring']
		paramq['skip_coran'] = self.params['skipcoran']
		paramq['init_method'] = self.params['initmethod']
		paramq['bin'] = self.params['bin']
		paramsdata = paramq.query(results=1)

		### create a norefRun object
		runq = appionData.ApNoRefRunData()
		runq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		# ... path makes the run unique:
		uniquerun = runq.query(results=1)
		if uniquerun and insert is True:
			apDisplay.printError("Run name '"+self.params['runname']+"' for stackid="+\
				str(self.params['stackid'])+"\nis already in the database")

		# ... continue filling non-unique variables:
		runq['name'] = self.params['runname']
		runq['stack'] = self.stack['data']
		runq['description'] = self.params['description']
		runq['hidden'] = False
		if paramsdata:
			runq['norefParams'] = paramsdata[0]
		else:
			runq['norefParams'] = paramq
		runq['run_seconds'] = self.runtime

		apDisplay.printMsg("inserting run parameters into database")
		if insert is True:
			runq.insert()

		### eigen data
		for i in range(self.params['numfactors']):
			factnum = i+1
			eigenq = appionData.ApCoranEigenImageData()
			eigenq['norefRun'] = runq
			eigenq['factor_num'] = factnum
			path = os.path.join(self.params['rundir'], "coran")
			eigenq['path'] = appionData.ApPathData(path=os.path.abspath(path))
			imgname = ("eigenimg%02d.png" % (factnum))
			eigenq['image_name'] = imgname
			if insert is True:
				if not os.path.isfile(os.path.join(path, imgname)):
					apDisplay.printWarning(imgname+" does not exist")
					continue
				eigenq['percent_contrib'] = self.contriblist[i]
				eigenq.insert()

		### particle align data
		if insert is True:
			apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		count = 0
		for partdict in self.partlist:
			count += 1
			if count % 100 == 0:
				if insert is True:
					sys.stderr.write(".")
				else:
					sys.stderr.write("x")
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
	def averageTemplate(self):
		"""
		takes the spider file and creates an average template of all particles and masks it
		"""
		emancmd  = "proc2d "+self.stack['file']+" template.mrc average edgenorm"
		apEMAN.executeEmanCmd(emancmd)

		templatefile = self.processTemplate("template.mrc")

		return templatefile

	#=====================
	def selectRandomParticles(self):
		"""
		takes the spider file and creates an average template of all particles and masks it
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
		takes the spider file and creates an average template of all particles and masks it
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
		takes the spider file and creates an average template of all particles and masks it
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
		### mask
		apDisplay.printMsg("Masking template by radius of "+str(self.params['maskrad'])+" Angstroms")
		emancmd  = ( "proc2d "+mrcfile+" "+mrcfile+" apix="+str(self.stack['apix'])
			+" mask="+str(self.params['maskrad']) )
		apEMAN.executeEmanCmd(emancmd)

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

		self.insertNoRefRun(insert=False)

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

		maskpixrad = self.params['maskrad']/self.stack['apix']/self.params['bin']
		esttime = apAlignment.estimateTime(self.params['numpart'], maskpixrad)
		apDisplay.printColor("Running spider this can take awhile, estimated time: "+\
			apDisplay.timeString(esttime),"cyan")

		### run the alignment
		aligntime = time.time()
		pixrad = int(round(self.params['partrad']/self.stack['apix']/self.params['bin']))
		alignedstack, self.partlist = alignment.refFreeAlignParticles(
			spiderstack, templatefile, 
			self.params['numpart'], pixrad,
			self.params['firstring'], self.params['lastring'])
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### remove large, worthless stack
		spiderstack = os.path.join(self.params['rundir'], "start.spi")
		apDisplay.printMsg("Removing un-aligned stack: "+spiderstack)
		apFile.removeFile(spiderstack, warn=False)

		### do correspondence analysis
		corantime = time.time()
		if not self.params['skipcoran']:
			maskpixrad = self.params['maskrad']/self.stack['apix']/self.params['bin']
			boxsize = int(math.floor(self.stack['boxsize']/self.params['bin']))
			self.contriblist = alignment.correspondenceAnalysis( alignedstack, 
				boxsize=boxsize, maskpixrad=maskpixrad, 
				numpart=self.params['numpart'], numfactors=self.params['numfactors'])
			### make dendrogram
			alignment.makeDendrogram(numfactors=self.params['numfactors'])
		corantime = time.time() - corantime


		inserttime = time.time()
		if self.params['commit'] is True:
			self.runtime = corantime + aligntime
			self.insertNoRefRun(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")
		inserttime = time.time() - inserttime

		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))
		apDisplay.printMsg("Correspondence Analysis time: "+apDisplay.timeString(corantime))
		apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

#=====================
if __name__ == "__main__":
	noRefAlign = NoRefAlignScript()
	noRefAlign.start()
	noRefAlign.close()

