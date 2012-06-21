#!/usr/bin/env python

#python
import re
import os
import sys
import glob
import shutil
#appion
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import appionScript
from appionlib import appiondata

"""
This file uploads particles to database that were
downloaded using the myamiweb interface
"""

#===========================
class UploadParticles(appionScript.AppionScript):
	def setupParserOptions(self):
		""" NEED TO COPY PARAM SETTING FROM ABOVE """

		self.parser.set_usage("Usage:\nuploadParticles.py <boxfiles> --bin=<n> --session=09dec07a\n")
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		self.parser.add_option("--filename", dest="filename",
			help="Path to Appion particle file", metavar="FILE")
		self.parser.add_option("--diam", dest="diam",
			help="particle diameter in angstroms", type="int")

	#===========================
	def checkConflicts(self):
		# check to make sure that incompatible parameters are not set
		if self.params['diam'] is None or self.params['diam']<=0:
			apDisplay.printError("Please input the diameter of your particle (for display purposes only)")

		# get list of input images, since wildcards are supported
		if self.params['filename'] is None:
			apDisplay.printError("Please enter the file name of Appion picked particle file")

		if self.params['sessionname'] is None:
			apDisplay.printError("Please enter Name of session to upload to, e.g., --session=09dec07a")
		self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "extract"

	#===========================
	def insertManualParams(self):

		runq = appiondata.ApSelectionRunData()
		runq['name'] = self.params['runname']
		runq['session'] = self.sessiondata
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		rundatas = runq.query(results=1)
		if rundatas and rundatas[0]['params']['diam'] != self.params['diam']:
			apDisplay.printError("upload diameter not the same as last run")

		manparams = appiondata.ApSelectionParamsData()
		manparams['diam'] = self.params['diam']
		runq['params'] = manparams

		if self.params['commit'] is True:
			apDisplay.printColor("Inserting manual selection run into database", "green")
			runq.insert()

		return runq

	#===========================
	def readFileToPeakTree(self):
		apDisplay.printMsg("Reading file: "+self.params['filename'])

		f = open(self.params['filename'], "r")
		count = 0
		imgfilename2peaklist = {}
		apDisplay.printMsg("Reading input file")
		for line in f:

			### format: x <tab> y <tab> filename
			sline = line.strip()
			cols = sline.split('\t')

			### must have 3 columns
			if len(cols) == 4:
				partid, xcoord, ycoord, filename = cols
			elif len(cols) == 3:
				xcoord, ycoord, filename = cols
			else:
				continue

			### check to make sure our x,y are integers, if not skip to next line in file
			try:
				xcoord = int(xcoord)
				ycoord = int(ycoord)
			except:
				continue

			### create new list for new files
			if not filename in imgfilename2peaklist.keys():
				imgfilename2peaklist[filename] = []

			peakdict = {
				'diameter': self.params['diam'],
				'xcoord': xcoord,
				'ycoord': ycoord,
				'peakarea': 10,
			}
			count += 1
			if count % 10 == 0:
				sys.stderr.write(".")

			imgfilename2peaklist[filename].append(peakdict)
		sys.stderr.write("done\n")
		f.close()
		apDisplay.printColor("Found %d particles in %d images"%
			(count, len(imgfilename2peaklist.keys())), "cyan")

		if count == 0:
			apDisplay.printError("No particles were found")

		return imgfilename2peaklist

	#===========================
	def start(self):
		imgfilename2peaklist = self.readFileToPeakTree()
		imglist = imgfilename2peaklist.keys()

		apDisplay.printMsg("Getting image data from database")
		imgtree = apDatabase.getSpecificImagesFromDB(imglist, self.sessiondata)
		if imgtree[0]['session']['name'] != self.sessiondata['name']:
			apDisplay.printError("Session and Image do not match "+imgtree[0]['filename'])	

		### insert params for manual picking
		rundata = self.insertManualParams()

		# upload Particles
		for imgdata in imgtree:
			### check session
			if imgdata['session']['name'] != self.sessiondata['name']:
				apDisplay.printError("Session and Image do not match "+imgdata['filename'])	

			peaktree = imgfilename2peaklist[imgdata['filename']]
			apDisplay.printMsg("%d particles for image %s"
				%(len(peaktree), apDisplay.short(imgdata['filename'])))
			if self.params['commit'] is True:
				apParticle.insertParticlePeaks(peaktree, imgdata, self.params['runname'], msg=True)

if __name__ == '__main__':
	uploadpart = UploadParticles()
	uploadpart.start()
	uploadpart.close()





