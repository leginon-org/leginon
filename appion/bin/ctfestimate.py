#!/usr/bin/env python

#pythonlib
import os
import re
import math
import time
import shutil
import subprocess
#appion
from appionlib import apFile
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib.apCtf import ctfdb
from appionlib.apCtf import ctfinsert

class ctfEstimateLoop(appionLoop2.AppionLoop):
	"""
	appion Loop function that
	runs Nico's CTFFIND or CTFTILT program
	to estimate the CTF in images
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctffind"
		if self.params['ctftilt'] is True:
			self.processdirname = "ctftilt"

	#======================
	def preLoopFunctions(self):
		self.ctfrun = None
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.logdir = os.path.join(self.params['rundir'], "logfiles")
		apParam.createDirectory(self.logdir, warning=False)
		self.ctfprgmexe = self.getCtfProgPath()
		return

	#======================
	def getCtfProgPath(self):
		unames = os.uname()
		exename = "ctffind"
		if self.params['ctftilt'] is True:
			exename = "ctftilt"
		if unames[-1].find('64') >= 0:
			exename += '64.exe'
		else:
			exename += "3.exe"
		ctfprgmexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
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
		time ./ctffind3.exe << eof
		micrograph.mrc
		montage.pow
		2.0, 200.0, 0.07, 60000, 7.0, 2 #! CS[mm], HT[kV], AmpCnst, XMAG, DStep[um], PAve
		128, 200.0, 8.0, 5000.0, 40000.0, 5000.0 #! Box, ResMin[A], ResMax[A], dFMin[A], dFMax[A], FStep
		eof

		CARD 1: Input file name for image
		CARD 2: Output file name to check result
		CARD 3: CS[mm], HT[kV], AmpCnst, XMAG, DStep[um],PAve
		CARD 4: Box, ResMin[A], ResMax[A], dFMin[A], dFMax[A], FStep,  dAst[A]
		CTFTILT also asks for TiltA[deg], TiltR[deg] at CARD4

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
		dAst: An additional parameter, dAst, was added to CARD 4 to restrain 
			the amount of astigmatism in the CTF fit. This makes the 
			fitting procedure more robust, especially in cases where 
			the Thon rings are not easily visible.
		TiltA: guessed tilt angle
		TiltR: angular range for initial coarse search 
		"""

		#get Defocus in Angstroms
		self.ctfvalues = {}
		if self.params['nominal'] is not None:
			nominal = abs(self.params['nominal']*1e4)
		else:
			nominal = abs(imgdata['scope']['defocus']*-1.0e10)
		ctfvalue = ctfdb.getBestCtfByResolution(imgdata)
		if ctfvalue is not None:
			"""
			## CTFFIND V3.5 (7-March-2012) prefers the smaller of the two values for astigmatic images
			I found that say you have an image with 1.1um and 1.5um defocus astigmatism. If you give 
			CTFFIND the average value of 1.3um for the defocus and 0.4um astig (dast) then it will 
			try to fit 1.3um and 1.8um, so you need to give it the minimum value (1.1um) for it to 
			fit 1.1um and 1.5um.
			"""
			bestdef = min(ctfvalue['defocus1'],ctfvalue['defocus2'])*1.0e10
		else:
			bestdef = nominal
	
		if ctfvalue is not None and self.params['bestdb'] is True:
			bestampcontrast = round(ctfvalue['amplitude_contrast'],3)
			beststigdiff = round(abs(ctfvalue['defocus1'] - ctfvalue['defocus2'])*1e10,1)
		else:
			bestampcontrast = self.params['amp'+self.params['medium']]
			beststigdiff = self.params['dast']

		if ctfvalue is not None and self.params['bestdb'] is True:
			### set res max from resolution_80_percent
			gmean = (ctfvalue['resolution_80_percent']*ctfvalue['resolution_50_percent']*self.params['resmax'])**(1/3.)
			if gmean < self.params['resmin']:
				# replace only if valid Issue #3291, #3547     
				self.params['resmax'] = round(gmean,2)
				apDisplay.printColor("Setting resmax to the geometric mean of resolution values", "purple")

		# dstep is the physical detector pixel size
		dstep = None
		if 'camera' in imgdata and imgdata['camera'] and imgdata['camera']['pixel size']:
			dstep = imgdata['camera']['pixel size']['x']
		if dstep is None:
			dstep = apDatabase.getPixelSize(imgdata)*imgdata['scope']['magnification']/10000.0
			dstep /=1e6
		dstep = float(dstep)
		mpixelsize = apDatabase.getPixelSize(imgdata)*1e-10
		if self.params['apix_man'] is not None:
			mpixelsize = self.params['apix_man']*1e-10
		xmag = dstep / mpixelsize
		apDisplay.printMsg("Xmag=%d, dstep=%.2e, mpix=%.2e"%(xmag, dstep, mpixelsize))
		inputparams = {
			'orig': os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc"),
			'input': apDisplay.short(imgdata['filename'])+".mrc",
			'output': apDisplay.short(imgdata['filename'])+"-pow.mrc",

			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'ampcnst': bestampcontrast,
			'xmag': xmag,
			'dstep': dstep*1e6,
			'pixavg': self.params['bin'],

			'box': self.params['fieldsize'],
			'resmin': self.params['resmin'],
			'resmax': self.params['resmax'],
			'defstep': self.params['defstep'], #round(defocus/32.0, 1),
			'dast': beststigdiff,
		}
		defrange = self.params['defstep'] * self.params['numstep'] ## do 25 steps in either direction
		inputparams['defmin']= round(bestdef-defrange, 1) #in meters
		if inputparams['defmin'] < 0:
			apDisplay.printWarning("Defocus minimum is less than zero")
			inputparams['defmin'] = inputparams['defstep']
		inputparams['defmax']= round(bestdef+defrange, 1) #in meters
		apDisplay.printColor("Defocus search range: %d A to %d A (%.2f to %.2f um)"
			%(inputparams['defmin'], inputparams['defmax'], 
			inputparams['defmin']*1e-4, inputparams['defmax']*1e-4), "cyan")

		### secondary lock check right before it starts on the real part
		if self.params['parallel'] and os.path.isfile(apDisplay.short(imgdata['filename'])+".mrc"):
			# This is a secondary image lock check, checking the first output of the process.
			# It alone is not good enough
			apDisplay.printWarning('Some other parallel process is working on the same image. Skipping')
			return
		### create local link to image
		if not os.path.exists(inputparams['input']):
			os.symlink(inputparams['orig'], inputparams['input'])

		### make standard input for ctf estimation
		line1cmd = inputparams['input']+"\n"
		line2cmd = inputparams['output']+"\n"
		line3cmd = (
			str(inputparams['cs'])+","
			+ str(inputparams['kv'])+","
			+ str(inputparams['ampcnst'])+","
			+ str(inputparams['xmag'])+","
			+ str(inputparams['dstep'])+","
			+ str(inputparams['pixavg'])+"\n")
		line4cmd = (
			str(inputparams['box'])+","
			+ str(inputparams['resmin'])+","
			+ str(inputparams['resmax'])+","
			+ str(inputparams['defmin'])+","
			+ str(inputparams['defmax'])+","
			+ str(inputparams['defstep'])+","
			+ str(inputparams['dast']))

		### additional ctftilt parameters
		if self.params['ctftilt'] is True:
			tiltang = apDatabase.getTiltAngleDeg(imgdata)
			line4cmd += (","+str(tiltang)+",10")
		line4cmd += "\n"

		if os.path.isfile(inputparams['output']):
			# program crashes if this file exists
			apFile.removeFile(inputparams['output'])

		t0 = time.time()
		apDisplay.printMsg("running ctf estimation at "+time.asctime())
		ctfproglog = os.path.join(self.logdir, os.path.splitext(imgdata['filename'])[0]+"-ctfprog.log")
		logf = open(ctfproglog, "w")
		ctfprogproc = subprocess.Popen(self.ctfprgmexe, shell=True, stdin=subprocess.PIPE, stdout=logf)
		apDisplay.printColor(self.ctfprgmexe, "magenta")
		apDisplay.printColor(line1cmd.strip(),"magenta")
		apDisplay.printColor(line2cmd.strip(),"magenta")
		apDisplay.printColor(line3cmd.strip(),"magenta")
		apDisplay.printColor(line4cmd.strip(),"magenta")
		ctfprogproc.stdin.write(line1cmd)
		ctfprogproc.stdin.write(line2cmd)
		ctfprogproc.stdin.write(line3cmd)
		ctfprogproc.stdin.write(line4cmd)
		ctfprogproc.communicate()
		logf.close()

		apDisplay.printMsg("ctf estimation completed in "+apDisplay.timeString(time.time()-t0))

		#apFile.removeFile(inputparams['input'])

		### parse ctf estimation output
		self.ctfvalues = {}
		logf = open(ctfproglog, "r")

		## ctffind & ctftilt have diff # values
		numvals = 6
		if self.params['ctftilt'] is True:
			numvals=8 
		for line in logf:
			sline = line.strip()
			if sline[-12:] == "Final Values":
				#print sline
				if '**********' in sline:
					sline = re.sub('**********', ' **********', sline)
				bits = sline.split()
				if len(bits) != numvals:
					apDisplay.printError("wrong number of values in "+str(bits))
				for i,bit in enumerate(bits[0:(numvals-2)]):
					bits[i] = float(bit)
				self.ctfvalues = {
					'defocus1':	float(bits[0])*1e-10,
					'defocus2':	float(bits[1])*1e-10,
					# WARNING: this is the negative of the direct result
					'angle_astigmatism':	float(bits[2]),
					'amplitude_contrast': inputparams['ampcnst'],
					'cross_correlation':	float(bits[numvals-3]),
					'nominal':	nominal*1e-10,
					'defocusinit':	bestdef*1e-10,
					'cs': self.params['cs'],
					'volts': imgdata['scope']['high tension'],
					'confidence': float(bits[numvals-3]),
					'confidence_d': round(math.sqrt(abs(float(bits[numvals-3]))), 5)
				}
				if self.params['ctftilt'] is True:
					self.ctfvalues['tilt_axis_angle']=float(bits[3])
					self.ctfvalues['tilt_angle']=float(bits[4])

		### write to log file
		f = open("ctfvalues.log", "a")
		f.write("=== "+imgdata['filename']+" ===\n")
		if not self.ctfvalues:
			nominaldf =  imgdata['scope']['defocus']
		else:
			nominaldf = self.ctfvalues['nominal']
		line1 = ("nominal=%.1e, bestdef=%.1e," %
			( nominaldf, self.ctfvalues['defocusinit']))
		if self.params['ctftilt'] is True:
			self.ctfvalues['origtiltang'] = tiltang
			line1+=" tilt=%.1f,"%tiltang
		apDisplay.printMsg(line1)
		f.write(line1)
		line2 = ("def_1=%.1e, def_2=%.1e, astig_angle=%.1f, cross_corr=%.3f,\n" %
			( self.ctfvalues['defocus1'], self.ctfvalues['defocus2'], self.ctfvalues['angle_astigmatism'],
				self.ctfvalues['cross_correlation'] ))
		if self.params['ctftilt'] is True:
			line2+= ("tilt_angle=%.1f, tilt_axis_angle=%.1f,\n" %
				(self.ctfvalues['tilt_angle'], self.ctfvalues['tilt_axis_angle']))
		apDisplay.printMsg(line2)
		f.write(line2)
		f.close()

		#convert powerspectra to JPEG
		outputjpgbase = os.path.basename(os.path.splitext(inputparams['output'])[0]+".jpg")
		self.lastjpg = outputjpgbase
		outputjpg = os.path.join(self.powerspecdir, self.lastjpg)
		powspec = apImage.mrcToArray(inputparams['output'])
		apImage.arrayToJpeg(powspec, outputjpg)
		shutil.move(inputparams['output'], os.path.join(self.powerspecdir, inputparams['output']))
		self.ctfvalues['graph1'] = outputjpg

		#apFile.removeFile(inputparams['input'])

		return

	#======================
	def commitToDatabase(self, imgdata):
		self.insertCtfTiltRun(imgdata)
		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrun, self.params['rundir'])

	#======================
	def insertCtfTiltRun(self, imgdata):
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# first create an aceparam object
		paramq = appiondata.ApCtfTiltParamsData()
		copyparamlist = ('medium','ampcarbon','ampice','fieldsize','cs','bin','resmin','resmax','defstep','dast')
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
						# float value such as cs of 4.1 is not quite equal
						if type(paramq[i]) == type(1.0) and abs(runnames[0]['ctftilt_params'][i]-paramq[i]) < 0.00001:
							continue
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
						apDisplay.printError("All parameters for a single CTF estimation run must be identical! \n"+\
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
	def setupParserOptions(self):
		self.parser.add_option("--ampcarbon", dest="ampcarbon", type="float", default=0.07,
			help="ampcarbon, default=0.07", metavar="#")
		self.parser.add_option("--ampice", dest="ampice", type="float", default=0.15,
			help="ampice, default=0.15", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="bin, default=1", metavar="#")
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int", default=256,
			help="fieldsize, default=256", metavar="#")
		self.parser.add_option("--medium", dest="medium", default="carbon",
			help="sample medium, default=carbon", metavar="MEDIUM")
		self.parser.add_option("--nominal", dest="nominal", type="float",
			help="nominal (in microns, absolute value)")
		self.parser.add_option("--newnominal", dest="newnominal", default=False,
			action="store_true", help="newnominal")
		self.parser.add_option("--resmin", dest="resmin", type="float", default=50.0,
			help="Low resolution end of data to be fitted", metavar="#")
		self.parser.add_option("--resmax", dest="resmax", type="float", default=15.0,
			help="High resolution end of data to be fitted", metavar="#")
		self.parser.add_option("--defstep", dest="defstep", type="float", default=1000.0,
			help="Step width for grid search in Angstroms", metavar="#")
		self.parser.add_option("--numstep", dest="numstep", type="int", default=25,
			help="Number of steps to search in grid", metavar="#")
		self.parser.add_option("--dast", dest="dast", type="float", default=100.0,
			help="dAst was added to CARD 4 to restrain the amount of astigmatism in \
				the CTF fit. This makes the fitting procedure more robust, especially \
				in cases where the Thon rings are not easily visible", metavar="#")
		self.parser.add_option("--apix_man", dest="apix_man", type="float",
			help="this option is optional and was added to manually change the pixel size value for \
				for each micrograph (NOT on the camera), i.e. at the specimen level for the mag. \
				Currently, this is only needed for Frealign and will replace the database entry",
				 metavar="#")

		## true/false
		self.parser.add_option("--ctftilt", dest="ctftilt", default=False,
			action="store_true", help="Run ctftilt instead of ctffind")
		self.parser.add_option("--bestdb", "--best-database", dest="bestdb", default=False,
			action="store_true", help="Use best amplitude contrast and astig difference from database")

	#======================
	def checkConflicts(self):
		if not (self.params['medium'] == 'carbon' or self.params['medium'] == 'ice'):
			apDisplay.printError("medium can only be 'carbon' or 'ice'")
		if self.params['resmin'] < 20.0:
			apDisplay.printError("Please choose a lower resolution for resmin")
		if self.params['resmax'] > 15.0 or self.params['resmax'] > self.params['resmin']:
			apDisplay.printError("Please choose a higher resolution for resmax")
		if self.params['defstep'] < 1.0 or self.params['defstep'] > 10000.0:
			apDisplay.printError("Please keep the defstep between 1 & 10000 Angstroms")
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		return

if __name__ == '__main__':
	imgLoop = ctfEstimateLoop()
	imgLoop.run()


