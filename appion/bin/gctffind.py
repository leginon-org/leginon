#!/usr/bin/env python

#pythonlib
import os
import re
import math
import time
import shutil
import subprocess
import traceback
#appion
from appionlib import apFile
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib import apDDprocess
from appionlib.apCtf import ctfdb
from appionlib.apCtf import ctfinsert
from appionlib.apCtf import ctffind4AvgRotPlot
from pyami import gctffindfun

class ctfEstimateLoop(appionLoop2.AppionLoop):
	"""
	appion Loop function that
	GCTFFIND is written by Shawn Zheng.
	Appion is Compatible with GCTFFIND 1.1.6
	"""

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--ampcontrast", dest="ampcontrast", type="float", default=0.07,
			help="ampcontrast, default=0.07", metavar="#")
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int", default=1024,
			help="fieldsize, default=1024", metavar="#")
		self.parser.add_option("--astig", dest="astig", type="float", default=0.05,
			help="astigmatism in fraction used to allow ratio of delta defocus to average", metavar="#")
		self.parser.add_option("--minphaseshift", "--min_phase_shift", dest="min_phase_shift", type="float", default=10.0,
			help="Minimum phase shift by phase plate, in degrees", metavar="#")
		self.parser.add_option("--maxphaseshift", "--max_phase_shift", dest="max_phase_shift", type="float", default=170.0,
			help="Maximum phase shift by phase plate, in degrees", metavar="#")

		## true/false
		self.parser.add_option("--bestdb", "--best-database", dest="bestdb", default=False,
			action="store_true", help="Use best amplitude contrast and astig difference from database")
		self.parser.add_option("--phaseplate", "--phase_plate", dest="shift_phase", default=False,
			action="store_true", help="Find additionalphase shift")
		
	#======================
	def checkConflicts(self):
		if self.params['astig'] > 1.0 or self.params['astig'] < 0:
			apDisplay.printError("Please choose an astigmatism as a ratio between 0 and 1")
			
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		return


	#======================
	def setProcessingDirName(self):
		self.processdirname = "gctffind"

	#======================
	def preLoopFunctions(self):
		self.ctfrun = None
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.logdir = os.path.join(self.params['rundir'], "logfiles")
		apParam.createDirectory(self.logdir, warning=False)
		self.exename = "gctffind"
		self.ctfprgmexe = self.getCtfProgPath()
		# check and process more often because it is slower than data collection
		self.setWaitSleepMin(1)
		self.setProcessBatchCount(1)
		return

	#======================
	def getCtfProgPath(self):
		exename = self.exename
		ctfprgmexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE, text=True).stdout.read().strip()
		if not os.path.isfile(ctfprgmexe):
			ctfprgmexe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(ctfprgmexe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		apDisplay.printMsg("Running program %s"%(exename))
		return ctfprgmexe

	#======================
	def postLoopFunctions(self):
		ctfdb.printCtfSummary(self.params, self.imgtree)

	#======================
	def reprocessImage(self, imgdata):
		"""
		Returns
		True, if an image should be reprocessed
		False, if an image was processed and should NOT be reprocessed
		None, if image has not yet been processed
		e.g. a confidence less than 80%
		"""
		if self.params['reprocess'] is None:
			return None
		ctfvalue, conf = ctfdb.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			return None
		if conf > self.params['reprocess']:
			return False
		else:
			return True

	#======================
	def processImage(self, imgdata):
		"""
		Input and output matches gctffind 1.1.6
		"""
		bestampcontrast = self.params['ampcontrast']
		self.ctfvalues = {}
		ctfvalue = ctfdb.getBestCtfByResolution(imgdata)
		best_defocus = imgdata['scope']['defocus'] * 1e10 # in angstrom
		if ctfvalue is not None and self.params['bestdb'] is True:
			if ctfvalue['amplitude_contrast'] > 0:
				bestampcontrast = round(ctfvalue['amplitude_contrast'],3)
				best_defocus = (ctfvalue['defocus1']+ctfvalue['defocus2'])/2
				apDisplay.printColor("Use best ctf amplitude contrast.", "purple")

		# dstep is the physical detector pixel size
		apix = apDatabase.getPixelSize(imgdata)

		# may be gain/dark corrected movie that has been binned
		origpath, binning = self.getOriginalPathAndBinning(imgdata)
		# ddstack might be binned.
		apix *= binning

		# inputparams defocii and astig are in Angstroms
		inputparams = self.params
		inputparams.update({
			'orig': origpath,
			'input': apDisplay.short(imgdata['filename'])+".mrc",
			'pow_output': apDisplay.short(imgdata['filename'])+"-pow.mrc",
			'ctf_output': apDisplay.short(imgdata['filename'])+".ctf.txt",

			'apix': apix,
			'volts': imgdata['scope']['high tension'],			
			'cs': self.params['cs'],
			'amplitude_contrast': bestampcontrast,
			'astig': self.params['astig'],
		})
		cmd = gctffindfun.makeCommand(self.ctfprgmexe, inputparams)

		### secondary lock check right before it starts on the real part
		if self.params['parallel'] and os.path.isfile(apDisplay.short(imgdata['filename'])+".mrc"):
			# This is a secondary image lock check, checking the first output of the process.
			# It alone is not good enough
			apDisplay.printWarning('Some other parallel process is working on the same image. Skipping')
			return
		### create local link to image
		if not os.path.exists(inputparams['input']):
			os.symlink(inputparams['orig'], inputparams['input'])

		if os.path.isfile(inputparams['pow_output']):
			# program crashes if this file exists
			apFile.removeFile(inputparams['pow_output'])

		t0 = time.time()
		apDisplay.printMsg("running ctf estimation at "+time.asctime())
		apDisplay.printColor("%s" % cmd,"magenta")
		print("")
		tdiff = time.time()-t0
		apDisplay.printColor(self.ctfprgmexe, "magenta")
		apDisplay.printColor(cmd,"magenta")
		gctffindfun.run(cmd, self.exename, inputparams['ctf_output'])

		### parse ctf estimation output
		self.ctfvalues = {}
		ctfproglog = inputparams['ctf_output']	
		apDisplay.printMsg("reading %s"%(ctfproglog))
		try:
			self.ctfvalues = gctffindfun.readResult(inputparams['ctf_output'])
		except:
			apDisplay.printWarning("Error reading %s"%(ctfproglog))
			self.setBadImage(imgdata)
			return
		self.ctfvalues.update({
			'imagenum': imgdata.dbid,
			'angle_astigmatism':	self.ctfvalues['angle_astigmatism']+90, # ????see bug #4047 for astig conversion
			'extra_phase_shift':	self.ctfvalues['extra_phase_shift']*math.pi/180.0, # radians
			'amplitude_contrast': inputparams['amplitude_contrast'],
			'cross_correlation':	self.ctfvalues['confidence'],
			'defocusinit':	best_defocus*1e-10,
			'cs': self.params['cs'],
			'volts': imgdata['scope']['high tension'],
			'confidence_d': round(math.sqrt(abs(self.ctfvalues['confidence'])), 5)
		})

		if len(list(self.ctfvalues.keys())) == 0:
			apDisplay.printWarning("Invalid %s"%(ctfproglog))
			self.setBadImage(imgdata)
			return

		#convert powerspectra to JPEG
		outputjpgbase = apDisplay.short(imgdata['filename'])+"-pow.jpg"
		self.lastjpg = outputjpgbase
		outputjpg = os.path.join(self.powerspecdir, self.lastjpg)
		powspec = apImage.mrcToArray(inputparams['pow_output'])
		apImage.arrayToJpeg(powspec, outputjpg)
		shutil.move(inputparams['pow_output'], os.path.join(self.powerspecdir, inputparams['pow_output']))
		self.ctfvalues['graph1'] = outputjpg

		##no avgrot file to convert to a PNG
		
		return

	#======================
	def commitToDatabase(self, imgdata):
		self.insertCtfRun(imgdata)
		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrun, self.params['rundir'])

	#======================
	def insertCtfRun(self, imgdata):
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# first create an aceparam object
		paramq = appiondata.ApGCtfFindParamsData()
		copyparamlist = ['ampcontrast','fieldsize','cs','shift_phase','astig']
		if self.params['shift_phase']:
			copyparamlist.extend(['min_phase_shift','max_phase_shift'])
		for p in copyparamlist:
			if p in self.params:
				paramq[p] = self.params[p]

		# create an acerun object
		runq = appiondata.ApAceRunData()
		runq['name'] = self.params['runname']
		runq['session'] = imgdata['session'];

		# see if acerun already exists in the database
		runnames = runq.query(results=1)

		if (runnames):
			prevrun = runnames[0]
			if not (prevrun['gctffind_params'] == paramq):
				for i in prevrun['gctffind_params']:
					if prevrun['gctffind_params'][i] != paramq[i]:
						# float value such as cs of 4.1 is not quite equal
						if type(paramq[i]) == type(1.0) and abs(prevrun['gctffind_params'][i]-paramq[i]) < 0.00001:
							continue
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
						apDisplay.printError("All parameters for a single CTF estimation run must be identical! \n"+\
						     "please check your parameter settings.")
			self.ctfrun = prevrun
			return False

		#create path
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['hidden'] = False
		# if no run entry exists, insert new run entry into db
		runq['gctffind_params'] = paramq
		runq.insert()
		self.ctfrun = runq
		return True

	def getOriginalPathAndBinning(self,imgdata):
		origPath = os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
		binning = 1
		return origPath, binning

if __name__ == '__main__':
	imgLoop = ctfEstimateLoop()
	imgLoop.run()


