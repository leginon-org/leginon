#!/usr/bin/env python

#python
import re
import os
import sys
import glob
import shutil
#appion
import apDisplay
import apDatabase
import apParticle
import appionScript
import appiondata



#===========================
def createDefaults():
	params={}
	self.params['apix']=None
	self.params['diam']=None
	self.params['bin']=None
	self.params['description']=None
	self.params['template']=None
	self.params['session']=None
	self.params['runname']=None
	self.params['imgs']=None
	self.params['abspath']=os.path.abspath('.')
	self.params['rescale']=False
	self.params['newbox']=None
	return params

#===========================
class UploadParticles(appionScript.AppionScript):
	def setupParserOptions(self):
		""" NEED TO COPY PARAM SETTING FROM ABOVE """

		self.parser.set_usage("Usage:\nuploadParticles.py <boxfiles> --bin=<n> --session=09dec07a\n")
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		self.parser.add_option("--files", dest="files",
			help="EMAN box files (wild cards ok), e.g., --files=/path/*.box", metavar="FILE")
		self.parser.add_option("--bin", dest="bin", default=1,
			help="If particles were picked on binned images, enter the binning factor", type='int')
		self.parser.add_option("--diam", dest="diam",
			help="particle diameter in angstroms", type="int")

	#===========================
	def checkConflicts(self):
		# check to make sure that incompatible parameters are not set
		if self.params['diam'] is None or self.params['diam']==0:
			apDisplay.printError("Please input the diameter of your particle (for display purposes only)")

		# get list of input images, since wildcards are supported
		if self.params['files'] is None:
			apDisplay.printError("Please enter the image names with picked particle files")

		if self.params['sessionname'] is None:
			apDisplay.printError("Please enter Name of session to upload to, e.g., --session=09dec07a")
		self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		self.processdirname = "extract"

	#=====================
	def setRunDir(self):
		path = os.path.abspath(self.sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		path = os.path.join(path, self.processdirname, self.params['runname'])
		self.params['rundir'] = path

	#===========================
	def getBoxFiles(self):
		# first get all box files
		filelist = glob.glob(self.params['files'])
		if len(filelist) == 0:
			apDisplay.printError("No images specified")
		boxfiles=[]
		for filename in filelist:
			if not os.path.isfile(filename):	
				apDisplay.printError("Could not find file: "+filename)
				continue
			if filename[-4:] != ".box":
				apDisplay.printWarning("File is not a boxfile: "+filename)

			boxfile = os.path.join(self.params['rundir'], os.path.basename(filename))
			apDisplay.printMsg("Copying file to "+boxfile)
			shutil.copy(filename, boxfile)
			boxfiles.append(boxfile)

		return boxfiles

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
	def boxFileToPeakTree(self, imgdata):
		boxfile = imgdata['filename']+".box"
		if not os.path.isfile(boxfile):
			apDisplay.printError("Could not find box file "+boxfile)
		f = open(boxfile, "r")
		peaktree = []
		for line in f:
			sline = line.strip()
			cols = sline.split()
			xcoord = float(cols[0]) * self.params['bin']
			ycoord = float(cols[1]) * self.params['bin']
			peakdict = {
				'diameter': self.params['diam'],
				'xcoord': xcoord,
				'ycoord': ycoord,
				'peakarea': 10,
			}
			peaktree.append(peakdict)
		return peaktree

	#===========================
	def start(self):
		apDisplay.printMsg("Getting box files")
		boxfiles = self.getBoxFiles()

		apDisplay.printMsg("Getting image data from database")
		imgtree = apDatabase.getSpecificImagesFromDB(boxfiles)
		if imgtree[0]['session']['name'] != self.sessiondata['name']:
			apDisplay.printError("Session and Image do not match "+imgtree[0]['filename'])	

		### insert params for manual picking
		rundata = self.insertManualParams()

		# upload Particles
		for imgdata in imgtree:
			### check session
			if imgdata['session']['name'] != self.sessiondata['name']:
				apDisplay.printError("Session and Image do not match "+imgdata['filename'])	

			peaktree = self.boxFileToPeakTree(imgdata)
			apParticle.insertParticlePeaks(peaktree, imgdata, self.params['runname'], msg=True)

if __name__ == '__main__':
	uploadpart = UploadParticles()
	uploadpart.start()
	uploadpart.close()





