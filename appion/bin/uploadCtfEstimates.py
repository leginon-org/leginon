#!/usr/bin/env python

#python
import os
import sys
#appion
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apInstrument
from appionlib import apParam
from appionlib.apCtf import ctfinsert

"""
This file uploads particles to database that were
downloaded using the myamiweb interface
"""

#===========================
class UploadCTF(appionScript.AppionScript):
	def setupParserOptions(self):
		self.parser.set_usage("Usage:\nuploadCtfEstimates.py\n")
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		self.parser.add_option("-f", "--filename", dest="filename",
			help="Path to Appion CTF dat file", metavar="FILE")

	#===========================
	def checkConflicts(self):
		# get list of input images, since wildcards are supported
		if self.params['filename'] is None or not os.path.exists(self.params['filename']):
			apDisplay.printError("Please enter a valid filename of Appion CTF dat file")
		if self.params['sessionname'] is None and self.params['expid'] is None:
			apDisplay.printError("Please enter session or expid to upload to, e.g., --session=09dec07a")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def insertCtfRun(self, imgdata):
		if isinstance(self.ctfrun, appiondata.ApAceRunData):
			return False

		# create an acerun object
		runq = appiondata.ApAceRunData()
		runq['name'] = self.params['runname']
		runq['session'] = imgdata['session'];

		# see if acerun already exists in the database
		runnames = runq.query(results=1)

		if (runnames):
			apDisplay.printError("Run name is already in use")

		#create path
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['hidden'] = False
		# if no run entry exists, insert new run entry into db
		if self.params['commit'] is True:
			runq.insert()
			self.ctfrun = runq
		return True


	#===========================
	def start(self):
		if self.params['sessionname'] is not None:
			self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		elif self.params['expid'] is not None:
			self.sessiondata = getSessionDataFromSessionId(self.params['expid'])
		self.params['cs'] = apInstrument.getCsValueFromSession(self.sessiondata)
		self.ctfrun = None
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)

		apDisplay.printMsg("Reading file: "+self.params['filename'])
		count = 0
		f = open(self.params['filename'], "r")
		for line in f:
			### format: x <tab> y <tab> filename
			sline = line.strip()
			if sline.startswith("image"):
				#skip first line
				continue
			cols = sline.split('\t')
			### must have exactly 12 columns
			if len(cols) == 12:
				imgid, nominal, def1, def2, angle, ampcont, res8, res5, conf30, conf5, conf, imgname = cols
			else:
				print "skipping line"
				continue
			imgid = int(imgid)
			imgdata = apDatabase.getImageDataFromSpecificImageId(imgid)

			if imgdata['session']['name'] != self.sessiondata['name']:
				apDisplay.printError("Session and Image do not match "+imgdata['filename'])
			if imgdata['filename'] != imgname:
				apDisplay.printError("Database and Datfile filename do not match "+imgdata['filename'])

			ctfvalues = {
				#'imagenum': imgid,
				'defocus2':	float(def2),
				'defocus1':	float(def1),
				'angle_astigmatism':	float(angle),
				'amplitude_contrast': float(ampcont),
				'ctffind4_resolution':	float(res8),
				'defocusinit':	float(nominal),
				'cs': self.params['cs'],
				'volts': imgdata['scope']['high tension'],
				'confidence': float(conf30),
				'confidence_d': float(conf5)
			}

			self.insertCtfRun(imgdata)
			if self.params['commit'] is True:
				ctfinsert.validateAndInsertCTFData(imgdata, ctfvalues, self.ctfrun, self.params['rundir'])

			count += 1
		f.close()
		apDisplay.printColor("Processed %d images"%(count), "cyan")

		if count == 0:
			apDisplay.printError("No images were processed")

if __name__ == '__main__':
	uploadctf = UploadCTF()
	uploadctf.start()
	uploadctf.close()





