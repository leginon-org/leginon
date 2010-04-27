#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import math
import time
import subprocess
import numpy
import socket
#appion
from appionlib import appionLoop2
from appionlib import appiondata
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apCtf
from appionlib import apParam
from appionlib import apFile

class AceTiltLoop(appionLoop2.AppionLoop):

	"""
	appion Loop function that
	runs Neil's acetilt program
	to estimate the CTF in images
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def preLoopFunctions(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.acetiltexe = self.getAceTiltPath()
		return

	#======================
	def getAceTiltPath(self):
		exename = 'acetilt.py'
		acetiltexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(acetiltexe):
			acetiltexe = os.path.join(apParam.getAppionDirectory(), 'ace2', exename)
		if not os.path.isfile(acetiltexe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return acetiltexe

	#======================
	def postLoopFunctions(self):
		pattern = os.path.join(self.params['rundir'], self.params['sessionname']+'*.corrected.mrc')
		apFile.removeFilePattern(pattern)
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
			return True

		ctfvalue, conf = apCtf.getBestCtfValueForImage(imgdata,msg=False,method="ace2")

		if ctfvalue is None:
			return True

		if conf > self.params['reprocess'] and ctfvalue['defocus1'] != ctfvalue['defocus2']:
			return False
		else:
			return True

	#======================

	def processImage(self, imgdata):

		bestdef, bestconf = apCtf.getBestCtfValueForImage(imgdata, msg=True, method="ace2")

		inputparams = {
			'input': os.path.join(imgdata['session']['image path'],imgdata['filename']+".mrc"),
			'cs': self.params['cs'],
			'kv': int(imgdata['scope']['high tension']/1000.0),
			'apix': apDatabase.getPixelSize(imgdata),
		}

		### make standard input for ACE 2
		apDisplay.printMsg("AceTilt executable: "+self.acetiltexe)
		commandline = ( self.acetiltexe
			+ " -f " + str(inputparams['input'])
			+ " -c " + str(inputparams['cs'])
			+ " -k " + str(inputparams['kv'])
			+ " -a " + str(inputparams['apix'])
			+ " -s " + str(self.params['splitsize'])
			+ " -n " + str(self.params['numsplits'])
			#+ " -e " + str(self.params['edge_b'])+","+str(self.params['edge_t'])
			+ "\n" )

		### run acetilt
		apDisplay.printMsg("running acetilt at "+time.asctime())
		apDisplay.printColor(commandline, "purple")

		t0 = time.time()

		if self.params['verbose'] is True:
			acetiltproc = subprocess.Popen(commandline, shell=True)
		else:
			aceoutf = open("acetilt.out", "a")
			aceerrf = open("acetilt.err", "a")
			acetiltproc = subprocess.Popen(commandline, shell=True, stderr=aceerrf, stdout=aceoutf)

		acetiltproc.wait()
		apDisplay.printMsg("acetilt completed in " + apDisplay.timeString(time.time()-t0))

		### check if acetilt worked
		imagelog = imgdata['filename']+".mrc"+".ctf.txt"

		if self.params['verbose'] is False:
			aceoutf.close()
			aceerrf.close()
		if not os.path.isfile(imagelog):
			apDisplay.printError("acetilt did not run")


		### parse log file
		self.ctfvalues = {}
		logf = open(imagelog, "r")
		for line in logf:
			sline = line.strip()
			if re.search("^Final Defocus:", sline):
				parts = sline.split()
				self.ctfvalues['defocus1'] = float(parts[2])
				self.ctfvalues['defocus2'] = float(parts[3])
				### convert to degrees
				self.ctfvalues['angle_astigmatism'] = math.degrees(float(parts[4]))
			elif re.search("^Amplitude Contrast:",sline):
				parts = sline.split()
				self.ctfvalues['amplitude_contrast'] = float(parts[2])
			elif re.search("^Confidence:",sline):
				parts = sline.split()
				self.ctfvalues['confidence'] = float(parts[1])
				self.ctfvalues['confidence_d'] = float(parts[1])
		logf.close()

		### summary stats
		apDisplay.printMsg("============")
		avgdf = (self.ctfvalues['defocus1']+self.ctfvalues['defocus2'])/2.0
		ampconst = 100.0*self.ctfvalues['amplitude_contrast']
		pererror = 100.0 * (self.ctfvalues['defocus1']-self.ctfvalues['defocus2']) / avgdf
		apDisplay.printMsg("Defocus: %.3f x %.3f um (%.2f percent astigmatism)"%
			(self.ctfvalues['defocus1']*1.0e6, self.ctfvalues['defocus2']*1.0e6, pererror ))
		apDisplay.printMsg("Angle astigmatism: %.2f degrees"%(self.ctfvalues['angle_astigmatism']))
		apDisplay.printMsg("Amplitude contrast: %.2f percent"%(ampconst))

		if bestconf is None:
			apDisplay.printMsg("Final confidence: %.3f"%(self.ctfvalues['confidence']))
		elif self.ctfvalues['confidence'] > bestconf:
			apDisplay.printMsg("Final (reprocessed) confidence: %.3f > %.3f"%(self.ctfvalues['confidence'],bestconf),'green')
		else:
			apDisplay.printMsg("Final (reprocessed) confidence: %.3f < %.3f"%(self.ctfvalues['confidence'],bestconf),'red')

		return

	#======================
	def commitToDatabase(self, imgdata):
		if self.ctfvalues is None:
			apDisplay.printWarning("ctf tilt failed to find any values")
			return False

		apDisplay.printMsg("Committing ctf parameters for "
			+apDisplay.short(imgdata['filename'])+" to database")

		paramq = appiondata.ApAceTiltParamsData()
		paramq['splitsize'] = self.params['splitsize']
		paramq['numsplits'] = self.params['numsplits']
		paramq['reprocess'] = self.params['reprocess']
		paramq['cs']      = self.params['cs']
		paramq['stig']    = True

		runq=appiondata.ApAceRunData()
		runq['name']    = self.params['runname']
		runq['session'] = imgdata['session']
		runq['hidden']  = False
		runq['path']    = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['acetilt_params'] = paramq

		ctfq = appiondata.ApCtfData()
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
		self.parser.add_option("-c", "--cs", dest="cs", type="float", default=2.0,
			help="Spherical aberation of the microscope", metavar="#")
		self.parser.add_option("--split-size", dest="splitsize", type="int", default=768,
			help="Size in pixels of areas to image", metavar="#")
		self.parser.add_option( "--num-splits", dest="numsplits", type="int", default=6,
			help="Number of divisions to divide image; -s 4 ==> 4x4 for 16 pieces", metavar="#")

		#self.parser.add_option("--edge1", dest="edge_b", type="float", default=12.0,
		#	help="Canny edge parameters Blur Sigma", metavar="#")
		#self.parser.add_option("--edge2", dest="edge_t", type="float", default=0.001,
		#	help="Canny edge parameters Edge Treshold(0.0-1.0)", metavar="#")

		### true/false
		self.parser.add_option("--verbose", dest="verbose", default=False,
			action="store_true", help="Show all acetilt messages")

		#self.parser.add_option("--refineapix", dest="refineapix", default=False,
		#	action="store_true", help="Refine the pixel size")

	#======================
	def checkConflicts(self):

		return


if __name__ == '__main__':
	imgLoop = AceTiltLoop()
	imgLoop.run()


