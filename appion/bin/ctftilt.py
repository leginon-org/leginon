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
import appionLoop2
import appiondata
import apImage
import apDisplay
import apDatabase
import apCtf
import apParam
import apFile

class ctfTiltLoop(appionLoop2.AppionLoop):
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
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.logdir = os.path.join(self.params['rundir'], "logfiles")
		apParam.createDirectory(self.logdir, warning=False)
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
		bestdef = apCtf.getBestDefocusForImage(imgdata, msg=True)*-1.0e10
		inputparams = {
			'orig': os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc"),
			'input': apDisplay.short(imgdata['filename'])+".mrc",
			'output': apDisplay.short(imgdata['filename'])+"-pow.mrc",

			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'ampcnst': self.params['amp'+self.params['medium']],
			'mag': float(imgdata['scope']['magnification']),
			'dstep': apDatabase.getPixelSize(imgdata)*imgdata['scope']['magnification']/10000.0,
			'pixavg': self.params['bin'],

			'box': self.params['fieldsize'],
			'resmin': 100.0,
			'resmax': 15.0,
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
		apDisplay.printMsg("running ctftilt at "+time.asctime())
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
				if '**********' in sline:
					sline = re.sub('**********', ' **********', sline)
				bits = sline.split()
				if len(bits) != 8:
					apDisplay.printError("wrong number of values in "+str(bits))
				for i,bit in enumerate(bits[0:6]):
					bits[i] = float(bit)
				self.ctfvalues = {
					'defocus1':	float(bits[0])*1e-10,
					'defocus2':	float(bits[1])*1e-10,
					'angle_astigmatism':	float(bits[2]),
					'tilt_axis_angle':	float(bits[3]),
					'tilt_angle':	float(bits[4]),
					'cross_correlation':	float(bits[5]),
					'nominal':	defocus*1e-10,
					'defocusinit':	bestdef*1e-10,
					'confidence_d':	round(math.sqrt(float(bits[5])), 5)
				}

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
		self.lastjpg = outputjpgbase
		outputjpg = os.path.join(self.params['rundir'], self.lastjpg)
		powspec = apImage.mrcToArray(inputparams['output'])
		apImage.arrayToJpeg(powspec, outputjpg)
		shutil.move(inputparams['output'], os.join(self.powerspecdir,inputparams['output']))
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
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# first create an aceparam object
		paramq = appiondata.ApCtfTiltParamsData()
		copyparamlist = ('medium','ampcarbon','ampice','fieldsize','cs','bin',)
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
			if not (runnames[0]['ctftilt_params'] == paramq):
				for i in runnames[0]['ctftilt_params']:
					if runnames[0]['ctftilt_params'][i] != paramq[i]:
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
				apDisplay.printError("All parameters for a single CtfTilt run must be identical! \n"+\
						     "please check your parameter settings.")
			self.ctfrun = runnames[0]
			return False

		#create path
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['hidden'] = False
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
		ctfq = appiondata.ApCtfData()
		ctfq['acerun'] = self.ctfrun
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
	def setupParserOptions(self):
		self.parser.add_option("--ampcarbon", dest="ampcarbon", type="float", default=0.07,
			help="ampcarbon, default=0.07", metavar="#")
		self.parser.add_option("--ampice", dest="ampice", type="float", default=0.15,
			help="ampice, default=0.15", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="bin, default=1", metavar="#")
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int", default=512,
			help="fieldsize, default=512", metavar="#")
		self.parser.add_option("--medium", dest="medium", default="carbon",
			help="sample medium, default=carbon", metavar="MEDIUM")
		self.parser.add_option("--cs", dest="cs", type="float", default=2.0,
			help="cs, default=2.0", metavar="#")
		self.parser.add_option("--nominal", dest="nominal",
			help="nominal")
		self.parser.add_option("--newnominal", dest="newnominal", default=False,
			action="store_true", help="newnominal")

	#======================
	def checkConflicts(self):
		if not (self.params['medium'] == 'carbon' or self.params['medium'] == 'ice'):
			apDisplay.printError("medium can only be 'carbon' or 'ice'")
		return

if __name__ == '__main__':
	imgLoop = ctfTiltLoop()
	imgLoop.run()


