#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import math
import cPickle
import time
import subprocess
import shutil
#appion
import appionLoop
import appionData
import apImage
import apDisplay
import apDatabase
import apCtf
import apParam
import apFile

class Ace2Loop(appionLoop.AppionLoop):
	
	"""
	appion Loop function that 
	runs Craig's ace2 program
	to estimate the CTF in images
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ace2"

	#======================
	def preLoopFunctions(self):
		self.ace2exe = self.getACE2Path()
		return

	#======================
	def getACE2Path(self):
		unames = os.uname()
		if unames[-1].find('64') >= 0:
			exename = 'ace2_64'
		else:
			exename = 'ace2_32'
		ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	 	if not os.path.isfile(ace2exe):
			ace2exe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	 	if not os.path.isfile(ace2exe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return ace2exe

	#======================
	def postLoopFunctions(self):
		apCtf.printCtfSummary(self.params)

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
		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			return None
		if conf > self.params['reprocess']:
			return False
		else:
			return True

	#======================
	
	def processImage(self, imgdata):

		bestdef = apCtf.getBestDefocusForImage(imgdata, display=True)*-1.0e10
		inputparams = {
		
			'input': os.path.join(imgdata['session']['image path'],imgdata['filename']+".mrc"),
			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'apix': apDatabase.getPixelSize(imgdata),
			'binby': self.params['bin'],

		}

		### make standard input for ctftilt
		
		print "Using ACE2 at:"+self.ace2exe
		commandline = ( self.ace2exe 
			+ " -i " + str(inputparams['input']) 
			+ " -b " + str(inputparams['binby']) 
			+ " -c " + str(inputparams['cs']) 
			+ " -k " + str(inputparams['kv'])  
			+ " -a " + str(inputparams['apix']) + "\n" )
		
		t0 = time.time()
		
		apDisplay.printMsg("running ace2 at "+time.asctime())
		
		ctftiltproc = subprocess.Popen(commandline, shell=True)	
		ctftiltproc.wait()

		apDisplay.printMsg("ace2 completed in " + apDisplay.timeString(time.time()-t0))
		
		self.ctfvalues = {}
		imagelog = imgdata['filename']+".mrc"+".ctf.txt"
		logf = open(imagelog, "r")
		lines = logf.readlines()

		for line in lines:
			sline = line.strip()
			if re.search("Defocus:", sline):
				parts = sline.split()
				self.ctfvalues['defocus1'] = float(parts[1])
				self.ctfvalues['defocus2'] = float(parts[2])
				self.ctfvalues['angle_astigmatism'] = float(parts[3])
			elif re.search("Amplitude Contrast:",sline):
				parts = sline.split()
				self.ctfvalues['amplitude_contrast'] = float(parts[2])
			elif re.search("Confidence:",sline):
				parts = sline.split()
				self.ctfvalues['confidence'] = float(parts[1])
				self.ctfvalues['confidence_d'] = float(parts[1])
		
		logf.close()
		
		print self.ctfvalues
		
		return

	#======================
	def commitToDatabase(self, imgdata):
		if self.ctfvalues is None:
			apDisplay.printWarning("ctf tilt failed to find any values")
			return False

		apDisplay.printMsg("Committing ctf parameters for "
			+apDisplay.short(imgdata['filename'])+" to database")

			('aceparams', ApAceParamsData),
			('ctftilt_params', ApCtfTiltParamsData),
			('ace2_params', ApAce2ParamsData),
			('session', leginondata.SessionData),
			('path', ApPathData),
			('name', str),
		)

		paramq = appionData.ApAce2ParamsData()
		paramq['bin']     = self.params['bin']
		paramq['reprocess'] = self.params['reprocess']
		paramq['cs']      = self.params['cs']

		runq=appionData.ApAceRunData()
		runq['name']    = self.params['runid']
		runq['session'] = imgdata['session']
		runq['path']    = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['ace2_params'] = paramq

		ctfq = appionData.ApCtfData()
		ctfq['acerun'] = runq
		ctfq['image']      = imgdata
		ctfq['mat_file'] = imgdata['filename']+".mrc.ctf.txt"
		ctfq['ctfvalues_file'] = imgdata['filename']+".mrc.norm.txt"
		ctfvaluelist = ('defocus1','defocus2','amplitude_contrast','angle_astigmatism','confidence','confidence_d')
		for i in range(len(ctfvaluelist)):
			key = ctfvaluelist[i]
			ctfq[key] = self.ctfvalues[key]

		ctfq.insert()
		return True

	#======================
	def specialDefaultParams(self):
		self.ctfrun = None
		self.params['bin'] =1
		self.params['cs'] = 2.0
		self.params['refine2d'] = False
		#self.params['refineapix'] = False

	#======================
	def specialCreateOutputDirs(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "powerspectra")
		apParam.createDirectory(self.powerspecdir, warning=False)
		#self.logdir = os.path.join(self.params['rundir'], "logfiles")
		#apParam.createDirectory(self.logdir, warning=False)
		return

	#======================
	def specialParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='help' or elements[0]=='--help' \
				or elements[0]=='-h' or elements[0]=='-help'):
				sys.exit(1)
			elif (elements[0]=='bin'):
				self.params['bin']=int(elements[1])
			elif (elements[0]=='cs'):
				self.params['cs']=float(elements[1])
			elif (arg=='refine2d'):
				self.params['refine2d']=True
			#elif (arg=='refineapix'):
			#	self.params['refineapix']=True
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	#======================
	def specialParamConflicts(self):
		if self.params['bin'] < 1:
			apDisplay.printError("bin must be positive")
		return


if __name__ == '__main__':
	imgLoop = Ace2Loop()
	imgLoop.run()

