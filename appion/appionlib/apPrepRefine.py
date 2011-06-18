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
		self.parser.add_option("-N", "--sp_lastParticle", dest="last", type="int", default=None,
			help="Number of particles to use", metavar="#")
		self.parser.add_option("--sp_lpFilter", dest="sp_lowpass", type="int", default=0,
			help="Low pass filter radius (in Angstroms) of the particles", metavar="#")
		self.parser.add_option("--sp_binning", dest="sp_bin", type="int", default=1,
			help="Binning of the particles", metavar="#")
		self.parser.add_option("--sp_hpFilter", dest="sp_highpass", type="int", default=0,
			help="High pass filter radius (in Angstroms) of the particles", metavar="#")
		# Initial 3D model manipulation
		self.parser.add_option("--modelid", dest="modelid", type="int",
			help="Initial model id from database")
		# Common refinement parameters
		self.parser.add_option('--sym', dest="sym", help="symmetry ")
		self.parser.add_option('--numiter', dest='numiter', type='int', default=1,
			help="number of refinement iterations to perform")
		self.parser.add_option('--mask', dest="mask", 
			help="mask from center of particle to outer edge (in Angstroms)")
		self.parser.add_option('--imask', dest="imask", default='0',
			help="inner mask radius (in Angstroms)")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['modelid'] is None:
			apDisplay.printError("model id was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new runname was not defined")
		self.params['totalpart'] = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		if 'last' not in self.params.keys() or self.params['last'] is None:
			self.params['last'] = self.params['totalpart']
		self.boxsize = apStack.getStackBoxsize(self.params['stackid'], msg=False)
		self.apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.refineboxsize = self.boxsize * self.params['sp_bin']
		### get the symmetry data
		if self.params['sym'] is None:
			apDisplay.printError("Symmetry was not defined")
		else:
			self.symmdata = apSymmetry.findSymmetry(self.params['sym'])
			self.params['symm_id'] = self.symmdata.dbid
			eman_symm_name = self.symmdata['eman_name']
			apDisplay.printMsg("Selected symmetry %s with id %s"%(eman_symm_name, self.symmdata.dbid))
			self.params['symm_name'] = self.convertSymmetryNameForPackage()
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		self.checkPackageConflicts()
		### convert iteration parameters first before its confict checking
		self.convertIterationParams()
		self.checkIterationConflicts()

	def checkIterationConflicts(self):
		''' 
		Conflict checking of per-iteration parameters
		'''
		maxmask = math.floor(self.apix*(self.boxsize-10)/2.0)
		print "maxmask",maxmask
		for iter in range(self.params['numiter']):
			if 'maskvol' not in self.params.keys():
				#maskvol is only settable by xmipp
				if self.params['mask'][iter] is None:
					apDisplay.printWarning("mask was not defined, setting to boxsize: %d"%(maxmask))
					self.params['mask'][iter] = maxmask
				if self.params['mask'][iter] > maxmask:
					apDisplay.printWarning("mask was too big, setting to boxsize: %d"%(maxmask))
					self.params['mask'][iter] = maxmask

	def checkPackageConflicts(self):
		'''
		Conflict checking of the single parameters specific to the refinement package
		'''
		pass

	def convertSymmetryNameForPackage(self):
		return self.symmdata['eman_name']

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
		'''
		takes the stack file and creates a stack file with binning and filtering
		ready for processing
		'''
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
		if self.params['sp_lowpass'] > 0:
			need_modify = True
			emancmd += "lp="+str(self.params['sp_lowpass'])+" "
		if self.params['sp_highpass'] > 0:
			need_modify = True
			emancmd += "hp="+str(self.params['sp_highpass'])+" "
		if self.params['last'] > 0 and self.params['last'] < self.params['totalpart']:
			need_modify = True
			emancmd += "last="+str(self.params['last']-1)+" "
		if self.params['sp_bin'] > 1:
			need_modify = True
			emancmd += "shrink="+str(self.params['sp_bin'])+" "
			clipsize = int(math.floor(self.stack['boxsize']/self.params['sp_bin']/2.0)*self.params['sp_bin']*2)
			emancmd += "clip="+str(clipsize)+","+str(clipsize)+"  edgenorm"+" "
			self.stack['boxsize'] = clipsize / self.params['sp_bin']

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
		self.stack['apix'] = self.stack['apix'] * self.params['sp_bin']
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
		in spider format so that it can not use this option in these functions
		'''
		self.spidersingle = False

	def setIterationParamList(self):
		self.iterparams = ['mask','imask']

	def tc(self,string):
		try:
			out = eval(string)
		except:
			string = string.strip()
			if string.upper() == 'T':
				out = True
			elif string.upper() == 'F':
				out = False
			else:
				out = string
		return out

	def convertIterationParams(self):
		self.setIterationParamList()
		for name in self.iterparams:
			param_str = str(self.params[name]).strip()
			param_upper = param_str.upper()
			multiple_bits = param_upper.split('X')
			if len(multiple_bits) <= 1:
				self.params[name] = map((lambda x: self.tc(param_str)),range(self.params['numiter']))
			else:
				self.params[name] = []
				set_bits = param_upper.split(':')
				position = 0
				total_repeat = 0
				for set in set_bits:
					m_index = set.find('X')
					try:
						repeat = int(set[:m_index])
						self.params[name].extend(map((lambda x:self.tc(param_str[position+m_index+1:position+len(set)])),range(repeat)))	
					except:
						self.params[name] = map((lambda x: self.tc(param_str)),range(self.params['numiter']))
					position += len(set)+1
			if len(self.params[name]) != self.params['numiter']:
				apDisplay.printError('Total number of parameter assignment must be equal to iteration number on parameter %s' % name)

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

