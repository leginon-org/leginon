#!/usr/bin/env python

#python
import os
import shutil
import time
import math
#appion
from appionlib import appionScript
from appionlib import appiondata
from leginon import leginondata
from appionlib import apFile
from appionlib import apModel
from appionlib import apVolume
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apInstrument

class Prep3DRefinement(appionScript.AppionScript):
	def onInit(self):
		self.refinemethod = None
		self.files_to_send = []

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stackid=ID --format=PROGRAM_NAME [options]")
		# Particle stack manipulation
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-N", "--lastParticle", dest="last", type="int", default=None,
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
		self.refineboxsize = self.boxsize * self.params['bin']
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		self.checkPackageConflicts()

	def checkPackageConflicts(self):
		'''
		Conflict checking of the single parameters specific to the refinement package
		'''
		pass

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
		if self.params['lowpass'] > 0:
			need_modify = True
			emancmd += "lp="+str(self.params['lowpass'])+" "
		if self.params['highpass'] > 0:
			need_modify = True
			emancmd += "hp="+str(self.params['highpass'])+" "
		if self.params['last'] > 0 and self.params['last'] < self.params['totalpart']:
			need_modify = True
			emancmd += "last="+str(self.params['last']-1)+" "
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
			outstackimg = outstack.replace('hed','img')
			if not os.path.isfile(imgstack):
				# only copy if not exist to save time
				shutil.copy(self.stack['file'].replace('hed','img'),outstackimg)
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
		self.model['format'] = extname
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

	def initializeStackModel(self):
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		self.stack['format'] = 'imagic'
		self.model = {}
		self.model['data'] = apModel.getModelFromId(self.params['modelid'])
		self.model['file'] = os.path.join(self.model['data']['path']['path'], self.model['data']['name'])
		self.model['apix'] = self.model['data']['pixelsize']
		self.model['format'] = self.model['data']['name'].split('.')[-1]

	def setProcessingDirName(self):
		self.processdirname = 'recon'

	def convertToRefineParticleStack(self):
		pass

	def saveFilesToSend(self):
		f = open(os.path.join(self.params['rundir'],'files_to_remote_host'), 'w')
		f.writelines(map((lambda x: x+'\n'),self.files_to_send))
		f.close()

	def commitRefineStack(self,prepdata):
		q = appiondata.ApRefineStackData()
		q['preprefine'] = prepdata
		q['stackref'] = self.stack['data']
		q['filename'] = os.path.basename(self.stack['file'])
		q['bin'] = self.params['bin']
		q['lowpass'] = self.params['lowpass']
		q['highpass'] = self.params['highpass']
		q['last_part'] = self.params['last']
		q['format'] = self.stack['format']
		q['apix'] = self.stack['apix']
		q['boxsize'] = self.stack['boxsize']
		q['cs'] = self.params['cs']  # This is the cs value that the ctf-corrected stack has used
		q['recon'] = False
		q.insert()

	def commitRefineInitModel(self,prepdata):
		q = appiondata.ApRefineInitModelData()
		q['preprefine'] = prepdata
		q['refmodel'] = self.model['data']
		q['filename'] = os.path.basename(self.model['file'])
		q['format'] = self.model['format']
		q['apix'] = self.model['apix']
		q.insert()

	def commitToDatabase(self):
		### create a prepRefine table
		prepq = appiondata.ApPrepRefineData()
		prepq['name'] = self.params['runname']
		prepq['hidden'] = False
		prepq['path'] = appiondata.ApPathData(path=self.params['rundir'])
		prepq['stack'] = appiondata.ApStackData.direct_query(self.params['stackid'])
		prepq['job'] = self.clusterjobdata
		prepq['session'] = leginondata.SessionData.direct_query(self.params['expid'])
		prepq['method'] = self.refinemethod
		prepq['description'] = self.params['description']
		if 'reconiterid' in self.params.keys() and self.params['reconiterid'] is not None:
			prepq['paramIter'] = appiondata.ApRefineIterData.direct_query(self.params['reconiterid'])
		r = prepq.query()
		if not r:
			prepq.insert()
			prepdata = prepq
		else:
			prepdata = r[0]
		
		self.commitRefineStack(prepdata)
		self.commitRefineInitModel(prepdata)

	def setFilesToSend(self):
		pass

	#=====================
	def start(self):
		self.initializeStackModel()
		self.setFormat()
		self.preprocessParticleStackWithProc2d()
		self.preprocessInitialModelWithProc3d()
		self.convertToRefineParticleStack()
		self.commitToDatabase()
		self.setFilesToSend()
		self.saveFilesToSend()
		
#=====================
if __name__ == "__main__":
	app = Prep3DRefinement()
	app.start()
	app.close()

