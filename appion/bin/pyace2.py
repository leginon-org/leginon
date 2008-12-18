#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import math
import time
import subprocess
import numpy
#appion
import appionLoop2
import appionData
import apImage
import apDisplay
import apDatabase
import apCtf
import apParam

class Ace2Loop(appionLoop2.AppionLoop):

	"""
	appion Loop function that
	runs Craig's ace2 program
	to estimate the CTF in images
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def preLoopFunctions(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "powerspectra")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.ace2exe = self.getACE2Path()
		return

	#======================
	def getACE2Path(self):
		unames = os.uname()
		if unames[-1].find('64') >= 0:
			exename = 'ace2_64.exe'
		else:
			exename = 'ace2_32.exe'
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

		#bestdef = apCtf.getBestDefocusForImage(imgdata, display=True)*-1.0e10
		inputparams = {
			'input': os.path.join(imgdata['session']['image path'],imgdata['filename']+".mrc"),
			'cs': self.params['cs'],
			'kv': imgdata['scope']['high tension']/1000.0,
			'apix': apDatabase.getPixelSize(imgdata),
			'binby': self.params['bin'],
		}

		### make standard input for ACE 2
		apDisplay.printMsg("Ace2 executable: "+self.ace2exe)
		commandline = ( self.ace2exe
			+ " -i " + str(inputparams['input'])
			+ " -b " + str(inputparams['binby'])
			+ " -c " + str(inputparams['cs'])
			+ " -k " + str(inputparams['kv'])
			+ " -a " + str(inputparams['apix']) + "\n" )

		### run ace2
		apDisplay.printMsg("running ace2 at "+time.asctime())
		apDisplay.printColor(commandline, "purple")
		aceoutf = open("ace2.out", "a")
		aceerrf = open("ace2.err", "a")
		t0 = time.time()
		ace2proc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
		ace2proc.wait()

		aceoutf.close()
		aceerrf.close()

		### check if ace2 worked
		imagelog = imgdata['filename']+".mrc"+".ctf.txt"
		if not os.path.isfile(imagelog) and self.stats['count'] <= 1:
			### ace2 always crashes on first image??? .fft_wisdom file??
			time.sleep(1)
			ace2proc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
			ace2proc.wait()
		if not os.path.isfile(imagelog):
			apDisplay.printError("ace2 did not run")
		apDisplay.printMsg("ace2 completed in " + apDisplay.timeString(time.time()-t0))

		### parse log file
		self.ctfvalues = {}
		logf = open(imagelog, "r")
		for line in logf:
			sline = line.strip()
			if re.search("Final Defocus:", sline):
				parts = sline.split()
				self.ctfvalues['defocus1'] = float(parts[2])
				self.ctfvalues['defocus2'] = float(parts[3])
				### convert to degrees
				self.ctfvalues['angle_astigmatism'] = math.degrees(float(parts[4]))
			elif re.search("Amplitude Contrast:",sline):
				parts = sline.split()
				self.ctfvalues['amplitude_contrast'] = float(parts[2])
			elif re.search("Confidence:",sline):
				parts = sline.split()
				self.ctfvalues['confidence'] = float(parts[1])
				self.ctfvalues['confidence_d'] = float(parts[1])
		logf.close()

		### summary stats
		apDisplay.printMsg("============")
		avgdf = (self.ctfvalues['defocus1']+self.ctfvalues['defocus2'])/2.0
		pererror = 100.0 * (self.ctfvalues['defocus1']-self.ctfvalues['defocus2']) / avgdf
		apDisplay.printMsg("Defocus: %.3f x %.3f um (%.2f percent error)"%
			(self.ctfvalues['defocus1']*1.0e6, self.ctfvalues['defocus2']*1.0e6, pererror ))
		apDisplay.printMsg("Angle astigmatism: %.2f degrees"%(self.ctfvalues['angle_astigmatism']))
		apDisplay.printMsg("Amplitude contrast: %.2f percent"%(100.0*self.ctfvalues['amplitude_contrast']))
		apDisplay.printMsg("Final confidence: %.3f"%(self.ctfvalues['confidence']))

		if avgdf < self.params['maxdefocus'] or avgdf > self.params['mindefocus']:
			apDisplay.printWarning("bad defocus estimate, not committing values to database")
			self.badprocess = True

		## create power spectra jpeg
		mrcfile = imgdata['filename']+".mrc.edge.mrc"
		if os.path.isfile(mrcfile):
			apDisplay.printMsg("Creating powerspectra jpeg")
			jpegfile = os.path.join(self.powerspecdir, imgdata['filename']+".jpg")
			ps = apImage.mrcToArray(mrcfile)
			ps = (ps-ps.mean())/ps.std()
			cutoff = -2.0*ps.min()
			ps = numpy.where(ps < cutoff, ps, cutoff)
			apImage.arrayToJpeg(ps, jpegfile)

		#print self.ctfvalues

		return

	#======================
	def commitToDatabase(self, imgdata):
		if self.ctfvalues is None:
			apDisplay.printWarning("ctf tilt failed to find any values")
			return False

		apDisplay.printMsg("Committing ctf parameters for "
			+apDisplay.short(imgdata['filename'])+" to database")

		paramq = appionData.ApAce2ParamsData()
		paramq['bin']     = self.params['bin']
		paramq['reprocess'] = self.params['reprocess']
		paramq['cs']      = self.params['cs']
		paramq['stig']    = True

		runq=appionData.ApAceRunData()
		runq['name']    = self.params['runname']
		runq['session'] = imgdata['session']
		runq['hidden']  = False
		runq['path']    = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['ace2_params'] = paramq

		ctfq = appionData.ApCtfData()
		ctfq['acerun'] = runq
		ctfq['image']      = imgdata
		ctfq['mat_file'] = imgdata['filename']+".mrc.ctf.txt"
		jpegfile = os.path.join(self.powerspecdir, imgdata['filename']+".jpg")
		if os.path.isfile(jpegfile):
			ctfq['graph1'] = imgdata['filename']+".jpg"
		ctfq['ctfvalues_file'] = imgdata['filename']+".mrc.norm.txt"
		ctfvaluelist = ('defocus1','defocus2','amplitude_contrast','angle_astigmatism','confidence','confidence_d')
		for i in range(len(ctfvaluelist)):
			key = ctfvaluelist[i]
			ctfq[key] = self.ctfvalues[key]

		ctfq.insert()
		return True

	#======================
	def setupParserOptions(self):
		### values
		self.parser.add_option("-b", "--bin", dest="bin", type="int", default=1,
			help="Binning of the image before FFT", metavar="#")
		self.parser.add_option("-c", "--cs", dest="cs", type="float", default=2.0,
			help="Spherical aberation of the microscope", metavar="#")
		self.parser.add_option("--mindefocus", dest="mindefocus", type="float", default=-0.1e-6,
			help="Minimal acceptable defocus (in meters)", metavar="#")
		self.parser.add_option("--maxdefocus", dest="maxdefocus", type="float", default=-10e-6,
			help="Maximal acceptable defocus (in meters)", metavar="#")
		### true/false
		self.parser.add_option("--refine2d", dest="refine2d", default=False,
			action="store_true", help="Refine the defocus after initial ACE with 2d cross-correlation")
		#self.parser.add_option("--refineapix", dest="refineapix", default=False,
		#	action="store_true", help="Refine the pixel size")

	#======================
	def checkConflicts(self):
		if self.params['bin'] < 1:
			apDisplay.printError("bin must be positive")
		if (self.params['mindefocus'] is not None and
				(self.params['mindefocus'] < -1e-3 or self.params['mindefocus'] > 1e-9)):
			apDisplay.printError("min defocus is not in an acceptable range, e.g. mindefocus=-1.5e-6")
		if (self.params['maxdefocus'] is not None and
				(self.params['maxdefocus'] < -1e-3 or self.params['maxdefocus'] > -1e-9)):
			apDisplay.printError("max defocus is not in an acceptable range, e.g. maxdefocus=-1.5e-6")

		return


if __name__ == '__main__':
	imgLoop = Ace2Loop()
	imgLoop.run()

