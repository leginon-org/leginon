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
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")

	#=====================
	def checkConflicts(self):
		if self.params['norefid'] is None:
			apDisplay.printError("No ref id was not defined")
		if self.params['numclass'] > 200:
			apDisplay.printError("too many classes defined: "+str(self.params['numclass']))

	#=====================
	def setOutDir(self):
		self.norefdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['outdir'] = os.path.join(uppath, "noref", self.params['runname'])

	#=====================
	def insertNoRefClassRun(self, insert=False):
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
		paramsdata = paramq.query(results=1)

		### create a norefRun object
		runq = appionData.ApNoRefRunData()
		runq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		# ... path makes the run unique:
		uniquerun = runq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+params['runname']+"' for stackid="+\
				str(params['stackid'])+"\nis already in the database")

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
			path = os.path.join(self.params['outdir'], "coran")
			eigenq['path'] = appionData.ApPathData(path=os.path.abspath(path))
			imgname = ("eigenimg%02d.png" % (factnum))
			eigenq['image_name'] = imgname
			if not os.path.isfile(os.path.join(path, imgname)):
				apDisplay.printWarning(imgname+" does not exist")
				continue
			eigenq['percent_contrib'] = self.contriblist[i]
			if insert is True:
				eigenq.insert()

		### particle align data
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
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

		return

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

		maskpixrad = self.params['maskrad']/self.stack['apix']
		esttime = apAlignment.estimateTime(self.params['numpart'], maskpixrad)
		apDisplay.printColor("Running spider this can take awhile, estimated time: "+\
			apDisplay.timeString(esttime),"cyan")

		#run the alignment
		aligntime = time.time()
		pixrad = int(round(self.params['partrad']/self.stack['apix']))
		alignedstack, self.partlist = alignment.refFreeAlignParticles(
			spiderstack, templatefile, 
			self.params['numpart'], pixrad,
			self.params['firstring'], self.params['lastring'])
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		#remove large, worthless stack
		spiderstack = os.path.join(self.params['outdir'], "start.spi")
		apDisplay.printMsg("Removing un-aligned stack: "+spiderstack)
		os.remove(spiderstack)

		#do correspondence analysis
		corantime = time.time()
		if not self.params['skipcoran']:
			maskpixrad = self.params['maskrad']/self.stack['apix']
			self.contriblist = alignment.correspondenceAnalysis( alignedstack, 
				boxsize=self.stack['boxsize'], maskpixrad=maskpixrad, 
				numpart=self.params['numpart'], numfactors=self.params['numfactors'])
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
	noRefClass = NoRefClassScript()
	noRefClass.start()
	noRefClass.close()

