#!/usr/bin/env python

#pythonlib
import os
import re
import sys
import math
import time
import shutil
import cPickle
#appion
from appionlib import apImage
from appionlib import apParam
from appionlib import apMatlab
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import appionLoop2
from appionlib import apInstrument
from appionlib.apCtf import ctfdb
from appionlib.apCtf import ctfinsert
try:
	import mlabraw as pymat
except:
	print "Matlab module did not get imported"

class aceLoop(appionLoop2.AppionLoop):
	#=====================
	def setProcessingDirName(self):
		self.processdirname = "ace"

	#=====================
	def preLoopFunctions(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.acerunq = None
		self.params['matdir']         = os.path.join(self.params['rundir'],"matfiles")
		self.params['tempdir']    = os.path.join(self.params['rundir'],"temp")
		apParam.createDirectory(os.path.join(self.params['matdir']), warning=False)
		apParam.createDirectory(os.path.join(self.params['tempdir']), warning=False)

		if self.params['sessionname'] is not None:
			self.params['outtextfile']=os.path.join(self.params['rundir'], self.params['sessionname']+".txt")
	
		if self.params['xvfb'] is True:
			apParam.resetVirtualFrameBuffer()
		apMatlab.checkMatlabPath(self.params)
		acepath = os.path.join(os.getcwd(), self.functionname+".py")
		#if not os.path.isfile(acepath):
		#	apDisplay.printWarning("'"+self.functionname+".py' usually needs to be run in the "+\
		#		"same directory as all of its matlab files")
		print "Connecting to matlab ... "
		if self.params['xvfb'] is True:
			apParam.resetVirtualFrameBuffer()
		try:
			self.matlab = pymat.open()
			#self.matlab = pymat.open('matlab -nodisplay')
		except:
			apDisplay.environmentError()
			raise
		apMatlab.setAceConfig(self.matlab, self.params)

	#=====================
	def postLoopFunctions(self):
		pymat.close(self.matlab)
		ctfdb.printCtfSummary(self.params, self.imgtree)

	#=====================
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

	#=====================
	def processImage(self, imgdata):
		self.ctfvalues = {}

		# RESTART MATLAB EVERY 500 IMAGES OR IT RUNS OUT OF MEMORY
		if self.stats['count'] % 500 == 0:
			apDisplay.printWarning("processed 500 images. restarting matlab...")
			pymat.close(self.matlab)
			time.sleep(5)
			self.matlab = pymat.open()

		scopeparams = {
			'kv':      imgdata['scope']['high tension']/1000,
			'apix':    apDatabase.getPixelSize(imgdata),
			'cs':      self.params['cs'],
			'tempdir': self.params['tempdir'],
		}
		### Scott's hack for FSU CM
		### For CM high tension is given in kv instead of v
		if imgdata['scope']['tem']['name'] == "CM":
			scopeparams['kv'] = imgdata['scope']['high tension']

		apMatlab.setScopeParams(self.matlab, scopeparams)
		### RUN ACE
		self.ctfvalues = {}
		acevalues = apMatlab.runAce(self.matlab, imgdata, self.params)

		#check if ACE was successful
		if acevalues[0] == -1:
			self.badprocess = True
			return False

		acevaluelist = ('defocus1','defocus2','defocusinit','amplitude_contrast','angle_astigmatism',
			'confidence','confidence_d')
		for i in range(len(acevaluelist)):
			self.ctfvalues[ acevaluelist[i] ] = acevalues[i]

		### override the astig angle to be in degrees
		self.ctfvalues['angle_astigmatism'] = - math.degrees(self.ctfvalues['angle_astigmatism'])
		self.ctfvalues['mat_file'] = imgdata['filename']+".mrc.mat"
		self.ctfvalues['cs'] = scopeparams['cs']
		self.ctfvalues['volts'] = scopeparams['kv']*1000.0

		### RENAME/MOVE OUTPUT FILES
		imfile1 = os.path.join(self.params['tempdir'], "im1.png")
		imfile2 = os.path.join(self.params['tempdir'], "im2.png")
		opimfile1 = imgdata['filename']+".mrc1.png"
		opimfile2 = imgdata['filename']+".mrc2.png"
		opimfilepath1 = os.path.join(self.powerspecdir, opimfile1)
		opimfilepath2 = os.path.join(self.powerspecdir, opimfile2)
		if os.path.isfile(imfile1):
			shutil.copyfile(imfile1, opimfilepath1)
		else:
			apDisplay.printWarning("imfile1 is missing, %s"%(imfile1))
		if os.path.isfile(imfile2):
			shutil.copyfile(imfile2, opimfilepath2)
		else:
			apDisplay.printWarning("imfile2 is missing, %s"%(imfile2))
		self.ctfvalues['graph1'] = opimfilepath1
		self.ctfvalues['graph2'] = opimfilepath2

	#=====================
	def commitToDatabase(self, imgdata):
		### PART 1: insert ACE run parameters
		if self.acerunq is None:
			self.insertACErunParams()

		ctfinsert.validateAndInsertCTFData(imgdata, self.ctfvalues, self.acerunq, self.params['rundir'])

		return

	#=====================
	def insertACErunParams(self):
		# first create an aceparam object
		aceparamq = appiondata.ApAceParamsData()
		for key in aceparamq.keys():
			if key in self.params:
				aceparamq[key] = self.params[key]

		# if nominal df is set, save override df to database, else don't set
		if self.params['nominal']:
			dfnom = abs(self.params['nominal'])
			aceparamq['df_override'] = dfnom

		# create an acerun object
		self.acerunq = appiondata.ApAceRunData()
		self.acerunq['name'] = self.params['runname']
		self.acerunq['session'] = self.getSessionData()

		# see if acerun already exists in the database
		acerundatas = self.acerunq.query(results=1)
		if (acerundatas):
			if not (acerundatas[0]['aceparams'] == aceparamq):
				for i in acerundatas[0]['aceparams']:
					if acerundatas[0]['aceparams'][i] != aceparamq[i]:
						apDisplay.printWarning("the value for parameter '"+str(i)+"' is different from before")
				apDisplay.printError("All parameters for a single ACE run must be identical! \n"+\
							  "please check your parameter settings.")

		#create path
		self.acerunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		self.acerunq['hidden'] = False
		self.acerunq['aceparams'] = aceparamq

		# if no run entry exists, insert new run entry into db
		self.acerunq.insert()

	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--edgethcarbon", dest="edgethcarbon", type="float", default=0.8,
			help="edge carbon, default=0.8", metavar="#")
		self.parser.add_option("--edgethice", dest="edgethice", type="float", default=0.6,
			help="edge ice, default=0.6", metavar="#")
		self.parser.add_option("--pfcarbon", dest="pfcarbon", type="float", default=0.9,
			help="pfcarbon, default=0.9", metavar="#")
		self.parser.add_option("--pfice", dest="pfice", type="float", default=0.3,
			help="pfice, default=0.3", metavar="#")
		self.parser.add_option("--overlap", dest="overlap", type="int", default=2,
			help="overlap, default=2", metavar="#")	
		self.parser.add_option("--fieldsize", dest="fieldsize", type="int", default=512,
			help="fieldsize, default=512", metavar="#")
		self.parser.add_option("--resamplefr", dest="resamplefr", type="float", default=1.5,
			help="resamplefr, default=1", metavar="#")
		self.parser.add_option("--drange", dest="drange", type="int", default=0,
			help="drange, default=0", metavar="#")
		self.parser.add_option("--medium", dest="medium", default="carbon",
			help="sample medium, default=carbon", metavar="MEDIUM")
		self.parser.add_option("--display", dest="display", type="int", default=1,
			help="display, default=1", metavar="#")
		self.parser.add_option("--stig", dest="stig", type="int", default=0,
			help="stig, default=0", metavar="#")
		self.parser.add_option("--nominal", dest="nominal", type="float",
			help="nominal")
		self.parser.add_option("--newnominal", dest="newnominal", default=False,
			action="store_true", help="newnominal")
		self.parser.add_option("--xvfb", dest="xvfb", default=False,
			action="store_true", help="xvfb")

	#=====================
	def checkConflicts(self):		
		if self.params['nominal'] is not None and (self.params['nominal'] > 0 or self.params['nominal'] < -15e-6):
			apDisplay.printError("Nominal should be of the form nominal=-1.2e-6 for -1.2 microns")
		if not (self.params['drange'] == 1 or self.params['drange']== 0):
			apDisplay.printError("drange should only be 0 or 1")
		if not (self.params['medium'] == 'carbon' or self.params['medium'] == 'ice'):
			apDisplay.printError("medium can only be 'carbon' or 'ice'")
		if not (self.params['display'] == 0 or self.params['display'] == 1):
			apDisplay.printError("display must be 0 or 1")
		if not (self.params['stig'] == 0 or self.params['stig'] == 1):
			apDisplay.printError("stig must be 0 or 1")
		### set cs value
		self.params['cs'] = apInstrument.getCsValueFromSession(self.getSessionData())
		return


if __name__ == '__main__':
	imgLoop = aceLoop()
	imgLoop.run()

