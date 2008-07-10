#!/usr/bin/python -O

#pythonlib
import os
import sys
import re
import math
import cPickle
import time
import subprocess
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

		inputparams = {
			'orig': os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc"),
			'input': apDisplay.short(imgdata['filename'])+".mrc",
			'output': apDisplay.short(imgdata['filename'])+"-pow.mrc",

			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'ampcnst': self.params['ampcnst '+self.params['medium']],
			'mag': float(imgdata['scope']['magnification']),
			'dstep': apDatabase.getPixelSize(imgdata)*imgdata['scope']['magnification']/10000.0,
			'pixavg': self.params['pixavg'],

			'box': self.params['fieldsize'],
			'resmin': 100.0,
			'resmax': 5.0,
			'defmin': round(defocus*0.8, 1),
			'defmax': round(defocus*1.2, 1),
			'defstep': 250.0, #round(defocus/32.0, 1),
		}
		t0 = time.time()
		cmd = "ln -s "+inputparams['orig']+" "+inputparams['input']+"\n"
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()

		#cmd += self.ctftiltexe+" << eof\n"
		#line1cmd = inputparams['orig']+"\n"
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
		#cmd += "eof\n"
		#cmd += ("mv "+inputparams['output']+" "
		#	+os.path.join(self.params['rundir'], "powerspectra", inputparams['output'])+"\n")
		#apDisplay.printColor(cmd, "cyan")

		### end tested

		ctftiltlog = os.path.splitext(imgdata['filename'])[0]+"-ctftilt.log"
		logf = open(ctftiltlog, "w")
		ctftiltproc = subprocess.Popen(self.ctftiltexe, shell=True, stdin=subprocess.PIPE, stdout=logf)
		ctftiltproc.stdin.write(line1cmd)
		ctftiltproc.stdin.write(line2cmd)
		ctftiltproc.stdin.write(line3cmd)
		ctftiltproc.stdin.write(line4cmd)
		ctftiltproc.wait()

		logf.close()
		apDisplay.printMsg("ctftilt completed in "+apDisplay.timeString(time.time()-t0))

		logf = open(ctftiltlog, "r")
		for line in logf:
			sline = line.strip()
			if sline[-12:] == "Final Values":
				#print sline
				bits = sline.split()
				if len(bits) != 8:
					apDisplay.printError("wrong number of values in "+str(bits))
				(def1, def2, astigang, tiltaxisang, tiltang, crosscor) = bits[0:6]
				print "nominal=", defocus, "tilt=", apDatabase.getTiltAngleDeg(imgdata)
				print "def1, def2, astigang, tiltaxisang, tiltang, crosscor"
				print def1, def2, astigang, tiltaxisang, tiltang, crosscor


		#read STDOUT
		#values DFMID1, DFMID2, ANGAST, TLTAXIS, TANGLE, CC

		#convert powerspectra to JPEG
		outputjpg = os.path.splitext(inputparams['output'])[0]+".jpg"
		powspec = apImage.mrcToArray(inputparams['output'])
		apImage.arrayToJpeg(powspec, outputjpg)

		#sys.exit(1)

		return

	#======================
	def commitToDatabase(self, imgdata):
		print ""
		#apCtf.insertAceParams(imgdata, self.params)
		#apCtf.commitCtfValueToDatabase(imgdata, self.matlab, self.ctfvalue, self.params)

	#======================
	def specialDefaultParams(self):
		self.params['ampcnst carbon']=0.07
		self.params['ampcnst ice']=0.15
		self.params['pixavg']=1
		self.params['fieldsize']=256
		self.params['medium']="carbon"
		self.params['cs']=2.0
		self.params['nominal']=None
		self.params['newnominal']=False

	#======================
	def specialCreateOutputDirs(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "powerspectra")
		apParam.createDirectory(self.powerspecdir, warning=False)

	#======================
	def specialParseParams(self,args):
		for arg in args:
			elements=arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='help' or elements[0]=='--help' \
				or elements[0]=='-h' or elements[0]=='-help'):
				sys.exit(1)
			elif (elements[0]=='ampcnst-carbon'):
				self.params['ampcnst carbon']=float(elements[1])
			elif (elements[0]=='ampcnst-ice'):
				self.params['ampcnst ice']=float(elements[1])
			elif (elements[0]=='overlap'):
				self.params['overlap']=int(elements[1])
			elif (elements[0]=='fieldsize'):
				self.params['fieldsize']=int(elements[1])
			elif (elements[0]=='pixavg'):
				self.params['pixavg']=int(elements[1])
			elif (elements[0]=='medium'):
				medium=elements[1]
				if medium is 'carbon' or medium is 'ice':
					self.params['medium']=medium
				else:
					apDisplay.printError("medium can only be 'carbon' or 'ice'")
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

