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

class ctfTiltLoop(appionLoop.AppionLoop):
	
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

		defocus = imgdata['scope']['defocus']*-1.0e10
		bestdef = apCtf.getBestDefocusForImage(imgdata, display=True)*-1.0e10
		inputparams = {
		
			'input': os.path.join(imgdata['session']['image path'],imgdata['filename']+".mrc"),
			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'apix': apDatabase.getPixelSize(imgdata),
			'binby': self.params['bin'],

		}
	
		### make standard input for ctftilt
		commandline = ace2exe + " -i " + str(inputparams['input']) + " -b " + str(inputparams['binby']) + " -c " + str(inputparams['cs']) + " -k " + str(inputparams['kv'])  + " -a " + str(inputparams['apix']) + "\n"
		
		t0 = time.time()
		
		apDisplay.printMsg("running ace2 at "+time.asctime())
		
		ctftiltlog = os.path.join(self.logdir,imgdata['filename']+".mrc"+".ctf.txt")
		logf = open(ctftiltlog, "w")
		
		ctftiltproc = subprocess.Popen(self.commandline, shell=True, stdin=subprocess.PIPE, stdout=logf)	
		ctftiltproc.wait()
		
		logf.close()

		apDisplay.printMsg("ace2 completed in " + apDisplay.timeString(time.time()-t0))

		### parse ctftilt output
		self.ctfvalues = {}
		logf = open(ctftiltlog, "r")
		lines = logf.readlines()
		
		re.search("Defocus: %f",params['defocus'],)
		
		for line in lines:
			sline = line.strip()
			if re.search("Defocus:", sline):
				float(sline)


		### write to log file
		f = open("ctfvalues.log", "a")
		f.write("=== "+imgdata['filename']+" ===\n")
		tiltang = apDatabase.getTiltAngleDeg(imgdata)
		line1 = ("nominal=%.1e, bestdef=%.1e, tilt=%.1f,\n" % 
			( self.ctfvalues['nominal'], self.ctfvalues['defocusinit'], tiltang))
		self.ctfvalues['origtiltang'] = tiltang
		print line1
		f.write(line1)
		line2 = ("def_1=%.1e, def_2=%.1e, astig_angle=%.1f,\ntilt_angle=%.1f, tilt_axis_angle=%.1f, cross_corr=%.3f,\n" % 
			( self.ctfvalues['defocus1'], self.ctfvalues['defocus2'], self.ctfvalues['angle_astigmatism'], 
				self.ctfvalues['tilt_angle'], self.ctfvalues['tilt_axis_angle'], self.ctfvalues['cross_correlation'] ))
		print line2
		f.write(line2)
		f.close()

		#convert powerspectra to JPEG
		outputjpgbase = os.path.basename(os.path.splitext(inputparams['output'])[0]+".jpg")
		self.lastjpg = os.path.join("powerspectra", outputjpgbase)
		outputjpg = os.path.join(self.params['rundir'], self.lastjpg)
		powspec = apImage.mrcToArray(inputparams['output'])
		apImage.arrayToJpeg(powspec, outputjpg)
		shutil.move(inputparams['output'], "powerspectra/"+inputparams['output'])
		
		return

	#======================
	def commitToDatabase(self, imgdata):
		print ""
		self.insertCtfRun(imgdata)
		self.insertCtfValues(imgdata)

	#======================
	def insertCtfRun(self, imgdata):
		if isinstance(self.ctfrun, appionData.ApCtfTiltRunData):
			return False

		# first create an aceparam object
		paramq = appionData.ApCtfTiltParamsData()
		copyparamlist = ('medium','ampcarbon','ampice','fieldsize','cs','bin',)
		for p in copyparamlist:
			if p in self.params:
				paramq[p] = self.params[p]

		# create an acerun object
		runq = appionData.ApCtfTiltRunData()
		runq['name'] = self.params['runid']
		runq['session'] = imgdata['session'];

		# see if acerun already exists in the database
		runids = runq.query(results=1)

		if (runids):
			if not (runids[0]['ctftilt_params'] == paramq):
				for i in runids[0]['ctftilt_params']:
					if runids[0]['ctftilt_params'][i] != paramq[i]:
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
				apDisplay.printError("All parameters for a single CtfTilt run must be identical! \n"+\
						     "please check your parameter settings.")
			self.ctfrun = runids[0]
			return False

		#create path
		runq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))

		# if no run entry exists, insert new run entry into db
		runq['ctftilt_params'] = paramq
		runq.insert()
		self.ctfrun = runq
		return True

	#======================
	def insertCtfValues(self, imgdata):
		if self.ctfvalues is None:
			apDisplay.printWarning("ctf tilt failed to find any values")
			return False

		print "Committing ctf parameters for",apDisplay.short(imgdata['filename']), "to database."
		ctfq = appionData.ApCtfData()
		ctfq['ctftiltrun'] = self.ctfrun
		ctfq['image']      = imgdata
		ctfq['graph1']     = self.lastjpg

		ctfvaluelist = ('defocus1','defocus2','defocusinit','angle_astigmatism',\
			'cross_correlation','tilt_angle','tilt_axis_angle','confidence_d')
		for i in range(len(ctfvaluelist)):
			key = ctfvaluelist[i]
			ctfq[ key ] = self.ctfvalues[key]
		ctfq.insert()
		return True


	#======================
	def specialDefaultParams(self):
		self.ctfrun = None
		self.params['ampcarbon']=0.07
		self.params['ampice']=0.15
		self.params['bin']=1
		self.params['fieldsize']=512
		self.params['medium']="carbon"
		self.params['cs']=2.0
		self.params['nominal']=None
		self.params['newnominal']=False

	#======================
	def specialCreateOutputDirs(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "powerspectra")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.logdir = os.path.join(self.params['rundir'], "logfiles")
		apParam.createDirectory(self.logdir, warning=False)

	#======================
	def specialParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='help' or elements[0]=='--help' \
				or elements[0]=='-h' or elements[0]=='-help'):
				sys.exit(1)
			elif (elements[0]=='-i'):
				self.params['input']=float(elements[1])
			elif (elements[0]=='bin'):
				self.params['bin']=int(elements[1])
			elif (elements[0]=='cs'):
				self.params['cs']=float(elements[1])
			else:
				apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	#======================
	def specialParamConflicts(self):
		if self.params['nominal'] is not None and (self.params['nominal'] > 0 or self.params['nominal'] < -15e-6):
			apDisplay.printError("Nominal should be of the form nominal=-1.2e-6 for -1.2 microns")
		return


if __name__ == '__main__':
	imgLoop = ctfTiltLoop()
	imgLoop.run()

