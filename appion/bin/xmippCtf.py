#!/usr/bin/env python

#pythonlib
import os
import re
import sys
import math
import time
import shutil
import cPickle
import subprocess
#appion
from pyami import spider
from appionlib import apFile
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
	runs Xmipp estimate_ctf_for_micrograph
	to estimate the CTF in images
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "xmippctf"

	#======================
	def preLoopFunctions(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.ctfrun = None
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())

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
		self.ctfvalues = {}
	
		### convert image to spider
		spiderimage = apDisplay.short(imgdata['filename'])+".spi"
		spider.write(imgdata['image'], spiderimage)

		### high tension in kiloVolts
		kvolts = imgdata['scope']['high tension']/1000.0
		### spherical aberration in millimeters
		cs = apInstrument.getCsValueFromSession(self.getSessionData())
		### pixel size in Angstroms
		apix = apDatabase.getPixelSize(imgdata)

		### write image name
		inputstr = ""
		inputstr += ("\n")
		inputstr += ("# image filename in spider format\n")
		inputstr += ("image=%s\n"%(spiderimage))

		### common parameters that never change
		inputstr += ("\n")
		inputstr += ("# common parameters that never change\n")
		inputstr += ("N_horizontal=%d\n"%(self.params['fieldsize']))
		#inputstr += ("particle_horizontal=%d\n"%(128))
		inputstr += ("show_optimization=yes\n")
		inputstr += ("micrograph_averaging=yes\n")

		""" Give a value in digital frequency (i.e. between 0.0 and 0.5)
			 This cut-off prevents the typically peak at the center of the PSD to interfere with CTF estimation.
			 The default value is 0.05, but for micrographs with a very fine sampling this may be lowered towards 0.0
		"""
		#minres = apix/minfreq => minfreq = apix/minres
		minfreq = apix/self.params['resmin']
		inputstr += ("min_freq=%.3f\n"%(minfreq))

		""" Give a value in digital frequency (i.e. between 0.0 and 0.5)
			 This cut-off prevents high-resolution terms where only noise exists to interfere with CTF estimation.
			 The default value is 0.35, but it should be increased for micrographs with signals extending beyond this value
		"""
		#maxres = apix/maxfreq => maxfreq = apix/maxres
		maxfreq = apix/self.params['resmax']
		inputstr += ("max_freq=%.3f\n"%(maxfreq))

		### CTF input parameters from database
		inputstr += ("\n")
		inputstr += ("# CTF input parameters from database\n")
		inputstr += ("voltage=%d\n"%(kvolts))
		inputstr += ("spherical_aberration=%.1f\n"%(cs))
		inputstr += ("sampling_rate=%.4f\n"%(apix))

		### best defocus in negative Angstroms
		ctfvalue, conf = ctfdb.getBestCtfValueForImage(imgdata, msg=True)
		if ctfvalue is None:
			apDisplay.printWarning("Xmipp CTF as implemented in Appion requires an initial CTF estimate to process"
				+"\nPlease run another CTF program first and try again on this image")
			self.ctfvalues = None
			return
		nominal = (ctfvalue['defocus1']+ctfvalue['defocus2'])/2.0
		inputstr += ("defocusU=%d\n"%(-abs(ctfvalue['defocus1'])*1.0e10))
		inputstr += ("defocusV=%d\n"%(-abs(ctfvalue['defocus2'])*1.0e10))
		inputstr += ("Q0=%d\n"%(-ctfvalue['amplitude_contrast']))
		inputstr += ("\n")

		### open and write to input parameter file
		paramfile = apDisplay.short(imgdata['filename'])+"-CTF.prm"
		f = open(paramfile, "w")
		print inputstr
		f.write(inputstr)
		f.close()

		#[min_freq=<f=0.05>]
		#[max_freq=<f=0.35>] 

		xmippcmd = "xmipp_ctf_estimate_from_micrograph -i %s"%(paramfile)

		#xmippcmd = "echo %s"%(paramfile)

		t0 = time.time()
		apDisplay.printMsg("running ctf estimation at "+time.asctime())
		proc = subprocess.Popen(xmippcmd, shell=True, stdout=subprocess.PIPE)
		#waittime = 2
		#while proc.poll() is None:
		#	sys.stderr.write(".")
		#	time.sleep(waittime)
		(stdout, stderr) = proc.communicate()
		#print (stdout, stderr)
		apDisplay.printMsg("ctf estimation completed in "+apDisplay.timeString(time.time()-t0))

		### read commandline output to get fit score
		lines = stdout.split('\n')
		lastline = ""
		for line in lines[-50:]:
			if "--->" in line:
				lastline = line
		if not "--->" in lastline:
			apDisplay.printWarning("Xmipp CTF failed")
			self.badprocess = True
			return
		bits = lastline.split('--->')
		confidence = float(bits[1])
		score = round(math.sqrt(1-confidence), 5)
		apDisplay.printColor("Confidence value is %.5f (score %.5f)"%(confidence, score), "cyan")

		f = open("confidence.log", "a")
		f.write("Confidence value is %.5f for image %s (score %.3f)\n"
			%(confidence, apDisplay.short(imgdata['filename']), score))
		f.close()

		### delete image in spider format no longer needed
		apFile.removeFile(spiderimage)

		### read output parameter file
		outparamfile = apDisplay.short(imgdata['filename'])+"_Periodogramavg.ctfparam"
		f = open(outparamfile, "r")
		for line in f:
			sline = line.strip()
			bits = sline.split('=')
			if sline.startswith("defocusU"):
				defocus1 = float(bits[1].strip())
			elif sline.startswith("defocusV"):
				defocus2 = float(bits[1].strip())
			elif sline.startswith("azimuthal_angle"):
				angle_astigmatism = float(bits[1].strip())
			elif sline.startswith("Q0"):
				amplitude_contrast = abs(float(bits[1].strip()))

		print defocus1, defocus2, angle_astigmatism, amplitude_contrast

		#defocusU=             -18418.6
		#defocusV=             -24272.1
		#azimuthal_angle=      79.7936
		#Q0=                   -0.346951 #negative of ACE amplitude_contrast
		print "AMP CONTRAST: %.4f -- %.4f"%(amplitude_contrast, ctfvalue['amplitude_contrast'])

		self.ctfvalues = {
			'defocus1':	defocus1*1e-10,
			'defocus2':	defocus2*1e-10,
			'angle_astigmatism':	angle_astigmatism,
			'amplitude_contrast':	amplitude_contrast,
			'nominal':	nominal,
			'defocusinit':	nominal,
			'confidence_d': score,
			'cs': self.params['cs'],
			'volts': kvolts*1000.0,
		}

		return

	#======================
	def commitToDatabase(self, imgdata):
		self.insertXmippCtfRun(imgdata)
		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.ctfrun, self.params['rundir'])

	#======================
	def insertXmippCtfRun(self, imgdata):
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# first create an aceparam object
		paramq = appiondata.ApXmippCtfParamsData()
		paramq['fieldsize'] = self.params['fieldsize']

		# create an acerun object
		runq = appiondata.ApAceRunData()
		runq['name'] = self.params['runname']
		runq['session'] = imgdata['session'];

		# see if acerun already exists in the database
		runnames = runq.query(results=1)

		if (runnames):
			if not (runnames[0]['xmipp_ctf_params'] == paramq):
				for i in runnames[0]['xmipp_ctf_params']:
					if runnames[0]['xmipp_ctf_params'][i] != paramq[i]:
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
				apDisplay.printError("All parameters for a single CTF estimation run must be identical! \n"+\
						     "please check your parameter settings.")
			self.ctfrun = runnames[0]
			return False

		#create path
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['hidden'] = False
		# if no run entry exists, insert new run entry into db
		runq['xmipp_ctf_params'] = paramq
		runq.insert()
		self.ctfrun = runq
		return True

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int", default=512,
			help="fieldsize, default=512", metavar="#")
		self.parser.add_option("--resmin", dest="resmin", type="float", default=100.0,
			help="Low resolution end of data to be fitted", metavar="#")
		self.parser.add_option("--resmax", dest="resmax", type="float", default=15.0,
			help="High resolution end of data to be fitted", metavar="#")

	#======================
	def checkConflicts(self):
		return

if __name__ == '__main__':
	imgLoop = ctfEstimateLoop()
	imgLoop.run()


