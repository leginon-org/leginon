#!/usr/bin/env python

#python
import os
import shutil
import time
import math
#appion
from appionlib import appionScript
from appionlib import apFile
from appionlib import apModel
from appionlib import apVolume
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apSymmetry
from appionlib import apInstrument

class Prep3DRefinement(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stackid=ID --format=PROGRAM_NAME [options]")
		# Particle stack manipulation
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int", default=0,
			help="Number of particles to use", metavar="#")
		self.parser.add_option("--lowpass", dest="lowpass", type="int", default=0,
			help="Low pass filter radius (in Angstroms) of the particles", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning of the particles", metavar="#")
		self.parser.add_option("--highpass", dest="highpass", type="int", default=0,
			help="High pass filter radius (in Angstroms) of the particles", metavar="#")
		# Initial 3D model manipulation
		self.parser.add_option("--modelid", dest="modelid", type="int",
			help="Initial model id from database")
		# Common refinement parameters
		self.parser.add_option('--mask', dest="mask", type='float',
			help="mask from center of particle to outer edge (in Angstroms)")
		self.parser.add_option('--imask', dest="imask", default=0, type='float',
			help="inner mask radius (in Angstroms")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['modelid'] is None:
			apDisplay.printError("model id was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new runname was not defined")
		if self.params['last'] is None:
			self.params['last'] = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		self.boxsize = apStack.getStackBoxsize(self.params['stackid'], msg=False)
		self.apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.refineboxsize = self.boxsize * self.params['bin']
		### get the symmetry data
		if self.params['sym'] is None:
			apDisplay.printError("Symmetry was not defined")
		else:
			self.symmdata = apSymmetry.findSymmetry(self.params['sym'])
			self.params['symm_id'] = self.symmdata.dbid
			self.params['symm_name'] = self.symmdata['eman_name']
			apDisplay.printMsg("Selected symmetry %s with id %s"%(self.symmdata['eman_name'], self.symmdata.dbid))
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		# general refinement masking of model per iteration
		maxmask = math.floor(self.apix*(self.boxsize-10)/2.0)
		if 'maskvol' not in self.params.keys():
			#maskvol is only settable by xmipp
			if self.params['mask'] is None:
				apDisplay.printWarning("mask was not defined, setting to boxsize: %d"%(maxmask))
				self.params['mask'] = maxmask
			if self.params['mask'] > maxmask:
				apDisplay.printWarning("mask was too big, setting to boxsize: %d"%(maxmask))
				self.params['mask'] = maxmask

	def proc2dFormatConversion(self):
		if self.spidersingle:
			extname = 'spi'
			format = 'spidersingle'
		else:
			extname = 'hed'
			format = ''
		return extname, format

	def proc3dFormatConversion(self):
		if self.spidersingle:
			extname = 'spi'
		else:
			extname = 'mrc'
		return extname

	def preprocessParticleStackWithProc2d(self):
		"""
		takes the stack file and creates a stack file with binning and filtering
		ready for processing
		"""
		need_modify = False
		emancmd  = "proc2d "
		if not os.path.isfile(self.stack['file']):
			apDisplay.printError("stackfile does not exist: "+self.stack['file'])
		emancmd += self.stack['file']+" "

		extname,addformat = self.proc2dFormatConversion()
		outstack = os.path.join(self.params['rundir'], "start.%s" % extname)
		apFile.removeFile(outstack, warn=True)
		emancmd += outstack+" "
		stackfilenamebits = self.stack['file'].split('.')
		oldextname = stackfilenamebits[-1]
		if extname != oldextname:
			need_modify = True
		if addformat:
			need_modify = True
			emancmd += addformat+" "

		emancmd += "apix="+str(self.stack['apix'])+" "
		if self.params['lowpass'] > 0:
			need_modify = True
			emancmd += "lp="+str(self.params['lowpass'])+" "
		if self.params['highpass'] > 0:
			need_modify = True
			emancmd += "hp="+str(self.params['highpass'])+" "
		if self.params['numpart'] > 0:
			need_modify = True
			emancmd += "last="+str(self.params['numpart']-1)+" "
		if self.params['bin'] > 1:
			need_modify = True
			emancmd += "shrink="+str(self.params['bin'])+" "
			clipsize = int(math.floor(self.stack['boxsize']/self.params['bin']/2.0)*self.params['bin']*2)
			emancmd += "clip="+str(clipsize)+","+str(clipsize)+"  edgenorm"+" "
			self.stack['boxsize'] = clipsize / self.params['bin']

		if need_modify:
			apFile.removeStack(outstack, warn=False)
			starttime = time.time()
			apDisplay.printColor("Running particle stack conversion.... This can take a while", "cyan")
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		else:
			# no need to execute EmanCmd if the stack is not modified
			shutil.copy(self.stack['file'],outstack)
		self.stack['file'] = outstack
		self.stack['apix'] = self.stack['apix'] * self.params['bin']
		return outstack
			
	def preprocessInitialModelWithProc3d(self):
		extname = self.proc3dFormatConversion()
		outmodelfile = os.path.join(self.params['rundir'], "initmodel.%s" % extname)
		apFile.removeStack(outmodelfile, warn=False)
		apVolume.rescaleVolume(self.model['file'], outmodelfile, self.model['apix'], self.stack['apix'], self.stack['boxsize'], spider=self.spidersingle)
		self.model['file'] = outmodelfile
		self.model['apix'] = self.stack['apix']
		return outmodelfile

	def setFormat(self):
		'''
		This is used in preprocessParticleStackWithProc2d
		and preprocessInitialModelWithProc3d
		that uses EMAN's proc2d and proc3d
		Thus far, only SPIDER 3D refinement can use self.spidersingle=True
		xmipp need to break the particles in folders even though it is also
		in spider format
		'''
		self.spidersingle = False

	def initializeStackModel(self):
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		self.model = {}
		self.model['data'] = apModel.getModelFromId(self.params['modelid'])
		self.model['file'] = os.path.join(self.model['data']['path']['path'], self.model['data']['name'])
		self.model['apix'] = self.model['data']['pixelsize']

	def setProcessingDirName(self):
		self.processdirname = 'recon'

	def convertToRefineParticleStack(self):
		pass

	def setupRefineScript(self):
		pass

	#=====================
	def start(self):
		self.initializeStackModel()
		self.setFormat()
		self.preprocessParticleStackWithProc2d()
		self.preprocessInitialModelWithProc3d()
		self.convertToRefineParticleStack()
		self.setupRefineScript()

#=====================
if __name__ == "__main__":
	app = Prep3DRefinement()
	app.start()
	app.close()

