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

#=====================
#=====================
#=====================
class Prep3DRefinement(appionScript.AppionScript):
	#=====================
	def onInit(self):
		self.setRefineMethod()
		self.files_to_send = []
		self.invert = False
		self.originalStackData = apStack.Stack( self.params['stackid'] )

	#=====================
	def setRefineMethod(self):
		'''
		Refine method will be used to classify the prepared run
		'''
		self.refinemethod = None

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
		# Initial 3D model manipulation usually only one
		self.parser.add_option("--modelid", dest="modelid", type="str", 	
			help="input model(s) use commas to separate multiples. i.e. '--modelid=1' or '--modelid=1,3,17', etc.", metavar="ID#(s)")

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
		self.modelids = map((lambda x: int(x)),self.params['modelid'].split(','))
		self.checkPackageConflicts()

	#=====================
	def checkPackageConflicts(self):
		'''
		Conflict checking of the single parameters specific to the refinement package
		'''
		pass

	#=====================
	def proc2dFormatConversion(self):
		# default is Imagic
		if self.stackspidersingle:
			extname = 'spi'
			format = 'spidersingle'
		else:
			extname = 'hed'
			format = ''
		return extname, format

	#=====================
	def proc3dFormatConversion(self):
		# default is mrc
		if self.modelspidersingle:
			extname = 'spi'
		else:
			extname = 'mrc'
		return extname

	#=====================
	def calcClipSize(slef,oldboxsize,bin):
		'''
		This keeps the clipsize dividable by binning
		'''
		clipsize = int(math.floor(oldboxsize/bin/2.0)*bin*2)
		if clipsize != oldboxsize:
			apDisplay.printWarning('Stack needs clipping before binning. May Corrupt coordinates!!!')
		return clipsize


	#=====================
	def preprocessStack(self):
		'''
		Use database particle stack file to create a stack file with binning and filtering
		ready for processing.
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
			clipsize = self.calcClipSize(self.stack['boxsize'],self.params['bin'])
			emancmd += "clip="+str(clipsize)+","+str(clipsize)+"  edgenorm"+" "
			self.stack['boxsize'] = clipsize / self.params['bin']
		if self.invert:
			need_modify = True
			emancmd += 'invert '
			
		if need_modify:
			apFile.removeStack(outstack, warn=False)
			starttime = time.time()
			apDisplay.printColor("Running particle stack conversion.... This can take a while", "cyan")
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		else:
			# no need to execute EmanCmd if the stack is not modified
			apDisplay.printColor("No stack pre-processing is needed. Copying stack to run directory.", "cyan")
			shutil.copy(self.stack['file'],outstack)
			outstackimg = outstack.replace('hed','img')
			if not os.path.isfile(outstackimg):
				# only copy if not exist to save time
				shutil.copy(self.stack['file'].replace('hed','img'),outstackimg)
		self.stack['file'] = outstack
		if not os.path.isfile(self.stack['file']):
			apDisplay.printColor("Could not locate stack: %s" % self.stack['file'], "cyan")
		self.stack['apix'] = self.stack['apix'] * self.params['bin']
		return outstack
			
	#=====================
	def preprocessModelWithProc3d(self, rescale=True):
		'''
		Use EMAN proc3d to scale initial or mask model to that of the refinestack and format
		'''
		extname = self.proc3dFormatConversion()
		if self.model['ismask'] is False:
			modelname = "initmodel"
		else:
			modelname = "maskvol"
		outmodelfile = os.path.join(self.params['rundir'], "%s%04d.%s" % (modelname,self.model['id'],extname))
		apFile.removeStack(outmodelfile, warn=False)
		if rescale:
			apVolume.rescaleVolume(self.model['file'], outmodelfile, self.model['apix'], self.stack['apix'], self.stack['boxsize'], spider=self.modelspidersingle)
		symmetry_description = self.model['data']['symmetry']['symmetry']
		if 'Icos' in symmetry_description:
			self.convertRefineModelIcosSymmetry(modelname,extname,outmodelfile,self.stack['apix'])
		self.model['file'] = outmodelfile
		self.model['apix'] = self.stack['apix']
		self.model['format'] = extname
		return outmodelfile

	#=====================
	def convertRefineModelIcosSymmetry(self,modelname,extname,modelfile,apix):
		'''
		This default conversion changes all to (2 3 5) Viper/3DEM convention.
		'''
		symmetry_description = self.model['data']['symmetry']['symmetry']
		# convert to (2 3 5) Viper/3DEM orientation
		if '(5 3 2)' in symmetry_description:
			tempfile = os.path.join(self.params['rundir'], "temp.%s" % (extname))
			apVolume.eman2viper(modelfile, tempfile, spider=self.modelspidersingle,apix=self.stack['apix'])
			shutil.copy(tempfile,modelfile)
		if '(2 5 3)' in symmetry_description:
			tempfile = os.path.join(self.params['rundir'], "temp.%s" % (extname))
			apVolume.crowther2viper(modelfile, tempfile, spider=self.modelspidersingle,apix=self.stack['apix'])
			shutil.copy(tempfile,modelfile)

	#=====================
	def setFormat(self):
		'''
		This is used to set output format in preprocessing.
		SPIDER 3D refinement use self.stackspidersingle=True and self.modelspidersingle=True.
		xmipp use self.modelspidersingle=True but self.stackspidersingle=False
		because it needs to be broken up into folders
		'''
		self.stackspidersingle = False
		self.modelspidersingle = False

	#=====================
	def __initializeStack(self):
		# This sets parameters of our new stack based on the params of the original stack
		# TODO: use originalStackData to populate these
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		self.stack['format'] = 'imagic'
		self.stack['phaseflipped'] = self.originalStackData.phaseFlipped
		self.stack['contrast'] = apStack.getParticleContrastFromStackId(self.params['stackid'])
		self.stack['kv'] = apStack.getKiloVoltsFromStackId(self.params['stackid'])

	#=====================
	def __initializeModel(self,modelid,ismask=False):
		self.model = {}
		self.model['data'] = apModel.getModelFromId(modelid)
		self.model['id'] = modelid
		self.model['file'] = os.path.join(self.model['data']['path']['path'], self.model['data']['name'])
		self.model['apix'] = self.model['data']['pixelsize']
		self.model['format'] = self.model['data']['name'].split('.')[-1]
		self.model['ismask'] = ismask

	#=====================
	def setProcessingDirName(self):
		self.processdirname = 'recon'

	#=====================
	def convertToRefineStack(self):
		'''
		Stack conversions that can not be achieved by proc2d
		'''
		pass

	#=====================
	def __saveFilesToSend(self):
		f = open(os.path.join(self.params['rundir'],'files_to_remote_host'), 'w')
		f.writelines(map((lambda x: x+'\n'),self.files_to_send))
		f.close()

	#=====================
	def __commitRefineStack(self,prepdata):
		'''
		Save parameters used to create refinestack in the database.
		Unlike a regular stack, Individual particle-refinestack relationship 
		is not committed to save time.
		'''
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
		q['phaseflipped'] = self.stack['phaseflipped']
		q.insert()

	#=====================
	def __commitRefineInitModel(self,prepdata):
		q = appiondata.ApRefineInitModelData()
		q['preprefine'] = prepdata
		q['refmodel'] = self.model['data']
		q['filename'] = os.path.basename(self.model['file'])
		q['format'] = self.model['format']
		q['apix'] = self.model['apix']
		q.insert()

	#=====================
	def __commitRefineMaskVol(self,prepdata):
		q = appiondata.ApRefineMaskVolData()
		q['preprefine'] = prepdata
		q['refmodel'] = self.model['data']
		q['filename'] = os.path.basename(self.model['file'])
		q['format'] = self.model['format']
		q['apix'] = self.model['apix']
		q.insert()

	#=====================
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
			prepq['paramiter'] = appiondata.ApRefineIterData.direct_query(self.params['reconiterid'])
		r = prepq.query()
		if not r:
			prepq.insert()
			prepdata = prepq
		else:
			prepdata = r[0]
		return prepdata

	#=====================
	def addToFilesToSend(self,filepath):
		basename = os.path.basename(filepath)
		self.files_to_send.append(basename)

	#=====================
	def addStackToSend(self,filepath):
		self.addToFilesToSend(filepath)

	#=====================
	def addModelToSend(self,filepath):
		self.addToFilesToSend(filepath)

	#=====================
	def __processStack(self,prepdata):
		'''
		Convert stack in database to refinestack in the format the refine method needs
		'''
		apDisplay.printColor("Step 3A: create self.stack dict with parameter info", "purple")		
		self.__initializeStack()
		
		### from original stack create a new stack file with binning and filtering ready for processing.
		### proc2d stuff, returns self.stack['file']
		### Neil: why is a value returned but not set
		apDisplay.printColor("Step 3B: from original stack create a new stack file"
			+" with binning and filtering ready for processing", "purple")				
		self.preprocessStack() 
		
		### if makeStack2 is needed (for things like ctf-correction changes)
		### Neil: why do we preprocess the stack if we just make a new one in the next step
		apDisplay.printColor("Step 3C: run makeStack2 if needed (for things like ctf-correction changes)", "purple")	
		self.convertToRefineStack()
		
		#Neil: why have a separate function to do one line?
		self.addStackToSend(self.stack['file'])
		self.__commitRefineStack(prepdata)

	#=====================
	def __processModel(self,prepdata,modelid,ismask=False):
		'''
		Convert model in database to refinemodel in the format required by the refine method
		and the scale it according to refinestack
		'''
		self.__initializeModel(modelid,ismask)
		self.preprocessModelWithProc3d()
		self.addModelToSend(self.model['file'])
		if not ismask:
			self.__commitRefineInitModel(prepdata)
		else:
			self.__commitRefineMaskVol(prepdata)

	#=====================
	def processMaskVol(self,prepdata):
		'''
		Additional process needed for the model used as mask volume.
		Only xmipp allows maskvolume for now.  It would be nice to do this
		for all refinement methods
		'''
		pass

	#=====================
	def preProcessPreparations(self):
		'''
		Place holder for any other preparation needed.
		Currently only Frealign may use this if initial euler angles
		come from a committed refinement iteration
		'''
		pass

	#=====================
	def otherPreparations(self):
		'''
		Place holder for any other preparation needed.
		Currently only Frealign may use this if initial euler angles
		come from a committed refinement iteration
		'''
		pass

	#=====================
	def start(self):
		apDisplay.printColor("Step 1: commit ApPrepRefineData to database", "purple")			
		prepdata = self.commitToDatabase()
		self.setFormat()
		
		apDisplay.printColor("Step 2: pre-process package specific preparations", "purple")
		self.preProcessPreparations()
		
		apDisplay.printColor("Step 3: manipulate stack for refinement", "purple")
		self.__processStack(prepdata)
		
		apDisplay.printColor("Step 4: manipulate models for refinement", "purple")
		for modelid in self.modelids:
			self.__processModel(prepdata,modelid,False)

		apDisplay.printColor("Step 5: process mask volume", "purple")			
		self.processMaskVol(prepdata)
		
		apDisplay.printColor("Step 6: other package specific preparations", "purple")
		self.otherPreparations()

		apDisplay.printColor("Step 7: save files to send", "purple")		
		self.__saveFilesToSend()

#=====================
#=====================		
#=====================
if __name__ == "__main__":
	app = Prep3DRefinement()
	app.start()
	app.close()

