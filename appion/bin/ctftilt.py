#!/usr/bin/python -O

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
import apImage
import apDisplay
import apDatabase
import apCtf
import apParam

class ctfTiltLoop(appionLoop.AppionLoop):
	"""
	appion Loop function that 
	runs Nico's CTFTILT program
	to estimate the CTF in tilted images
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctftilt"

	#======================
	def preLoopFunctions(self):
		self.ctftiltexe = self.getCtfTiltPath()
		return

	#======================
	def getCtfTiltPath(self):
		unames = os.uname()
		if unames[-1].find('64') >= 0:
			exename = 'ctftilt64.exe'
		else:
			exename = 'ctftilt32.exe'
		ctftiltexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	 	if not os.path.isfile(ctftiltexe):
			ctftiltexe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	 	if not os.path.isfile(ctftiltexe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return ctftiltexe

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
		"""
		time ./ctffind3.exe << eof
		micrograph.mrc
		montage.pow
		2.0, 200.0, 0.07, 60000, 7.0, 2						! CS[mm], HT[kV], AmpCnst, XMAG, DStep[um], PAve
		128, 200.0, 8.0, 5000.0, 30000.0, 1000.0	! Box, ResMin[A], ResMax[A], dFMin[A], dFMax[A], FStep
		eof

		CTFTILT - determines defocus, astigmatism tilt axis and tilt angle
		for images of arbitrary size (MRC format). Astigmatic angle is measured
		from x axis (same conventions as in the MRC 2D image processing 
		programs).

		CARD 1: Input file name for image
		CARD 2: Output file name to check result
		CARD 3: CS[mm], HT[kV], AmpCnst, XMAG, DStep[um],PAve
		CARD 4: Box, ResMin[A], ResMax[A], dFMin[A], dFMax[A], FStep

		The output image file to check the result of the fitting
		shows the filtered average power spectrum of the input
		image in one half, and the fitted CTF (squared) in the
		other half. The two halves should agree very well for a
		successful fit.

		CS: Spherical aberration coefficient of the objective in mm
		HT: Electron beam voltage in kV
		AmpCnst: Amount of amplitude contrast (fraction). For ice
			images 0.07, for negative stain about 0.15.
		XMAG: Magnification of original image
		DStep: Pixel size on scanner in microns, or apix*mag/10000
		PAve: Pixel averaging (PAve x PAve) for input image

		Box: Tile size. The program divides the image into square
			tiles and calculates the average power spectrum. Tiles
			with a significantly higher or lower variance are 
			excluded; these are parts of the image which are unlikely
			to contain useful information (beam edge, film number 
			etc). IMPORTANT: Box must have a even pixel dimensions.
		ResMin: Low resolution end of data to be fitted.
		ResMaX: High resolution end of data to be fitted.
		dFMin: Starting defocus value for grid search in Angstrom. 
			Positive values represent an underfocus. The program
			performs a systematic grid search of defocus values 
			and astigmatism before fitting a CTF to machine 
			precision.
		dFMax: End defocus value for grid search in Angstrom.
		FStep: Step width for grid search in Angstrom.
		"""

		#get Defocus in Angstroms

		defocus = imgdata['scope']['defocus']*-1.0e10
		bestdef = apCtf.getBestDefocusForImage(imgdata, display=True)*-1.0e10
		inputparams = {
			'orig': os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc"),
			'input': apDisplay.short(imgdata['filename'])+".mrc",
			'output': apDisplay.short(imgdata['filename'])+"-pow.mrc",

			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'ampcnst': self.params['ampcnst '+self.params['medium']],
			'mag': float(imgdata['scope']['magnification']),
			'dstep': apDatabase.getPixelSize(imgdata)*imgdata['scope']['magnification']/10000.0,
			'pixavg': self.params['bin'],

			'box': self.params['fieldsize'],
			'resmin': 100.0,
			'resmax': 5.0,
			'defmin': round(bestdef*0.8, 1),
			'defmax': round(bestdef*1.2, 1),
			'defstep': 500.0, #round(defocus/32.0, 1),
		}

		### create local link to image
		if not os.path.exists(inputparams['input']):
			cmd = "ln -s "+inputparams['orig']+" "+inputparams['input']+"\n"
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
	
		### make standard input for ctftilt
		line1cmd = inputparams['input']+"\n"
		line2cmd = inputparams['output']+"\n"
		line3cmd = (
			str(inputparams['cs'])+","
			+ str(inputparams['kv'])+","
			+ str(inputparams['ampcnst'])+","
			+ str(inputparams['mag'])+","
			+ str(inputparams['dstep'])+","
			+ str(inputparams['pixavg'])+"\n")
		line4cmd = (
			str(inputparams['box'])+","
			+ str(inputparams['resmin'])+","
			+ str(inputparams['resmax'])+","
			+ str(inputparams['defmin'])+","
			+ str(inputparams['defmax'])+","
			+ str(inputparams['defstep'])+"\n")

		if os.path.isfile(inputparams['output']):
			# program crashes if this file exists
			apFile.removeFile(inputparams['output'])

		t0 = time.time()
		apDisplay.printMsg("running ctftilt")
		ctftiltlog = os.path.join(self.logdir, os.path.splitext(imgdata['filename'])[0]+"-ctftilt.log")
		logf = open(ctftiltlog, "w")
		ctftiltproc = subprocess.Popen(self.ctftiltexe, shell=True, stdin=subprocess.PIPE, stdout=logf)
		ctftiltproc.stdin.write(line1cmd)
		ctftiltproc.stdin.write(line2cmd)
		ctftiltproc.stdin.write(line3cmd)
		ctftiltproc.stdin.write(line4cmd)
		ctftiltproc.wait()
		logf.close()

		apDisplay.printMsg("ctftilt completed in "+apDisplay.timeString(time.time()-t0))

		#apFile.removeFile(inputparams['input'])

		### parse ctftilt output
		self.ctfvalues = {}
		logf = open(ctftiltlog, "r")
		for line in logf:
			sline = line.strip()
			if sline[-12:] == "Final Values":
				#print sline
				bits = sline.split()
				if len(bits) != 8:
					apDisplay.printError("wrong number of values in "+str(bits))
				for i,bit in enumerate(bits[0:6]):
					bits[i] = float(bit)
				self.ctfvalues = {
					'defocus1':	float(bits[0]),
					'defocus2':	float(bits[1]),
					'angle_astigmatism':	float(bits[2]),
					'tilt_axis_angle':	float(bits[3]),
					'tilt_angle':	float(bits[4]),
					'cross_correlation':	float(bits[5]),
					'nominal':	defocus,
					'defocusinit':	bestdef,
					'confidence_d':	math.sqrt(float(bits[5]))
				}

		### write to log file
		f = open("ctfvalues.log", "a")
		f.write("=== "+imgdata['filename']+" ===\n")
		tiltang = apDatabase.getTiltAngleDeg(imgdata)
		line1 = ("nominal=%.1f, bestdef=%.1f, tilt=%.1f,\n" % 
			( self.ctfvalues['nominal'], self.ctfvalues['defocusinit'], tiltang))
		self.ctfvalues['origtiltang'] = tiltang
		print line1
		f.write(line1)
		line2 = ("def_1=%.1f, def_2=%.1f, astig_angle=%.1f,\ntilt_angle=%.1f, tilt_axis_angle=%.1f, cross_corr=%.1f,\n" % 
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
		#apFile.removeFile(inputparams['input'])

		#sys.exit(1)

		return

	#======================
	def commitToDatabase(self, imgdata):
		print ""
		#apCtf.insertAceParams(imgdata, self.params)
		self.insertCtfTiltRun(imgdata)
		#apCtf.commitCtfValueToDatabase(imgdata, self.matlab, self.ctfvalue, self.params)
		self.insertCtfValues(imgdata)

	#======================
	def insertCtfTiltRun(self, imgdata):
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
	def insertCtfValue(self, imgdata):
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
			ctfq[ ctfvaluelist[i] ] = self.ctfvalues[i]
		ctfq.insert()
		return True


	#======================
	def specialDefaultParams(self):
		self.ctfrun = None
		self.params['ampcnst carbon']=0.07
		self.params['ampcnst ice']=0.15
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
			elif (elements[0]=='ampcarbon'):
				self.params['ampcnst carbon']=float(elements[1])
			elif (elements[0]=='ampice'):
				self.params['ampcnst ice']=float(elements[1])
			elif (elements[0]=='overlap'):
				self.params['overlap']=int(elements[1])
			elif (elements[0]=='fieldsize'):
				self.params['fieldsize']=int(elements[1])
			elif (elements[0]=='bin'):
				self.params['bin']=int(elements[1])
			elif (elements[0]=='medium'):
				medium=elements[1]
				if medium == 'carbon' or medium == 'ice':
					self.params['medium']=medium
				else:
					apDisplay.printError("medium can only be 'carbon' or 'ice', NOT "+medium)
			elif (elements[0]=='cs'):
				self.params['cs']=float(elements[1])
			elif (elements[0]=='nominal'):
				self.params['nominal']=float(elements[1])
			elif (elements[0]=='newnominal'):
				self.params['newnominal']=True
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

