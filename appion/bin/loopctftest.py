#!/usr/bin/env python

#pythonlib
import os
import re
import math
import time
import shutil
import subprocess
import random
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

class ctfEstimateLoop(appionLoop2.AppionLoop):
	"""
	appion Loop function that fakes a ctffind4 run
	"""

	#======================
	def setupParserOptions(self):
		## true/false
		self.parser.add_option("--bestdb", "--best-database", dest="bestdb", default=False,
			action="store_true", help="Use best amplitude contrast and astig difference from database")
		
	#======================
	def checkConflicts(self):
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		return


	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def preLoopFunctions(self):
		self.ctfrun = None
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.logdir = os.path.join(self.params['rundir'], "logfiles")
		apParam.createDirectory(self.logdir, warning=False)
		# check and process more often because it is slower than data collection
		self.setWaitSleepMin(1)
		self.setProcessBatchCount(1)
		return

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
		"""
		# dstep is the physical detector pixel size
		apix = apDatabase.getPixelSize(imgdata)

		# may be gain/dark corrected movie that has been binned
		origpath, binning = self.getOriginalPathAndBinning(imgdata)
		# ddstack might be binned.
		apix *= binning

		inputparams = {
			'orig': origpath,
			'input': apDisplay.short(imgdata['filename'])+".mrc",
			'output': apDisplay.short(imgdata['filename'])+"-pow.mrc",

			'apix': apix,
			'kv': imgdata['scope']['high tension']/1000.0,			
			'cs': self.params['cs'],
			'ampcontrast': 0.07,
		}

		### secondary lock check right before it starts on the real part
		if self.params['parallel'] and os.path.isfile(apDisplay.short(imgdata['filename'])+".mrc"):
			# This is a secondary image lock check, checking the first output of the process.
			# It alone is not good enough
			apDisplay.printWarning('Some other parallel process is working on the same image. Skipping')
			return
		### create local link to image
		if not os.path.exists(inputparams['input']):
			os.symlink(inputparams['orig'], inputparams['input'])

		if os.path.isfile(inputparams['output']):
			# program crashes if this file exists
			apFile.removeFile(inputparams['output'])

		t0 = time.time()
		apDisplay.printMsg("running ctf estimation at "+time.asctime())

		### parse ctf estimation output
		self.ctfvalues = {}
		bestdef = imgdata['scope']['defocus']
		defocus1 = abs(imgdata['scope']['defocus']*1e10)+random.randrange(10)*0.1 - 0.5
		defocus2 = abs(imgdata['scope']['defocus']*1e10)+random.randrange(10)*0.1 - 0.5
		ctf_res = random.randrange(10)*0.3 + 2.0
		bits = [imgdata.dbid,defocus1,defocus2,10.0,0.0,0.9,ctf_res]
		if True:
			self.ctfvalues = {
				'imagenum': int(float(bits[0])),
				'defocus2':	float(bits[1])*1e-10,
				'defocus1':	float(bits[2])*1e-10,
				'angle_astigmatism':	float(bits[3])+90, # see bug #4047 for astig conversion
				'extra_phase_shift':	float(bits[4]), # radians
				'amplitude_contrast': inputparams['ampcontrast'],
				'cross_correlation':	float(bits[5]),
				'ctffind4_resolution':	self.convertCtffind4Resolution(bits[6]),
				'defocusinit':	bestdef*1e-10,
				'cs': self.params['cs'],
				'volts': imgdata['scope']['high tension'],
				'confidence': float(bits[5]),
				'confidence_d': round(math.sqrt(abs(float(bits[5]))), 5)
			}

		if len(self.ctfvalues.keys()) == 0:
			apDisplay.printWarning("Invalid %s"%(ctfproglog))
			self.setBadImage(imgdata)
			return
		return

	def convertCtffind4Resolution(self,res_str):
		res_float = float(res_str)
		# ctffind4 output inf if not well fitted
		if res_float == float('inf'):
			# return a number as database can not take inf
			return 100000.0
		return res_float

	#======================
	def commitToDatabase(self, imgdata):
		self.insertCtfRun(imgdata)
		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrun, self.params['rundir'])

	#======================
	def insertCtfRun(self, imgdata):
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# first create an aceparam object
		paramq = appiondata.ApCtfFind4ParamsData()
		copyparamlist = ['ampcontrast','fieldsize','cs','bestdb','resmin','defstep','shift_phase']
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
			if not (prevrun['ctffind4_params'] == paramq):
				for i in prevrun['ctffind4_params']:
					if prevrun['ctffind4_params'][i] != paramq[i]:
						# float value such as cs of 4.1 is not quite equal
						if type(paramq[i]) == type(1.0) and abs(prevrun['ctffind4_params'][i]-paramq[i]) < 0.00001:
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
		runq['ctffind4_params'] = paramq
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


