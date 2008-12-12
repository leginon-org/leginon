#!/usr/bin/env python
# Upload tomograms to the database

import os
import sys
import time
import re
import shutil
import appionScript
import apUpload
import apParam
import apFile
import apDisplay
import apDatabase
import apRecon
import apVolume
import apProject

#=====================
#=====================
class UploadTomoScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog --file=<filename> --session=<name> --symm=<#> \n\t "
			+" --res=<#> --description='text' [--contour=<#>] [--zoom=<#>] \n\t "
			+" [--rescale=<model ID,scale factor> --boxsize=<#>] ")
		self.parser.add_option("-i", "--image", dest="image", 
			help="snapshot image file to upload", metavar="IMAGE")
		self.parser.add_option("-f", "--file", dest="file", 
			help="MRC file to upload", metavar="FILE")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--name", dest="name",
			help="File name for new tomogram, automatically set")
		self.parser.add_option("-t", "--tiltseries", dest="tiltseriesnumber",
			help="Tilt Series # for a given session, Manually specified", metavar="TILTSERIES")
		self.parser.add_option("-v", "--volume", dest="volume",
			help="Subvolume from original voxel volume", metavar="VOLUME")

	#=====================
	def checkConflicts(self):
		if self.params['tiltseriesnumber'] is None:
			apDisplay.printError("Enter a Tilt Series")
		if self.params['volume'] is None:
			apDisplay.printError("Enter a Tomo Volume name")
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['description'] is None:
			apDisplay.printError("Enter a description of the initial model")
		elif self.params['file'] is not None:
			if not os.path.isfile(self.params['file']):
				apDisplay.printError("could not find file: "+self.params['file'])
			if self.params['file'][-4:] != ".mrc":
				apDisplay.printError("uploadModel.py only supports MRC files")
			self.params['file'] = os.path.abspath(self.params['file'])
		else:
			apDisplay.printError("Please provide a tomogram .mrc to upload")

	#=====================
	def setRunDir(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries" +  self.params['tiltseriesnumber']
		tomovolumepath = self.params['volume']
		intermediatepath = os.path.join(tiltseriespath,tomovolumepath)
		self.params['rundir'] = os.path.join(path,intermediatepath)

	#=====================
	def setNewFileName(self, unique=False):
		#clean up old name
		basename = os.path.basename(self.params['file'])
		basename = re.sub(".mrc", "", basename)
		self.params['name'] = basename
		
		#clean up old name
		if self.params['image']:
			snapshotname = os.path.basename(self.params['image'])
			snapshotname = re.sub(".png", "", snapshotname)

	#=====================
	def checkExistingFile(self):
		newtomopath = os.path.join(self.params['rundir'], self.params['name']+".mrc")
		origtomopath = self.params['file']
		apDisplay.printWarning("A Tomogram by the same filename already exists: '"+newtomopath+"'")
		### a model by the same name already exists
		mdnew = apFile.md5sumfile(newtomopath)
		mdold = apFile.md5sumfile(origtomopath)
		if mdnew != mdold:
			### they are different, make unique name
			self.setNewFileName(unique=True)
			apDisplay.printWarning("The tomograms are different, cannot overwrite, so using new name: %s" % (self.params['name'],))
			# restart
			self.start()
			return True
		elif apDatabase.isTomoInDB(mdnew):
			### they are the same and its in the database already
			apDisplay.printWarning("Same Tomogram with md5sum '"+mdnew+"' already exists in the database!")
			self.params['commit'] = False
			self.params['chimeraonly'] = True
		else:
			### they are the same, but its not in the database
			apDisplay.printWarning("The same tomogram with name '"+newtomopath+"' already exists, but is not uploaded!")
			if self.params['commit'] is True:
				apDisplay.printMsg("Inserting tomogram into database...")

	#=====================
	def start(self):
		if self.params['name'] is None:
			self.setNewFileName()
		apDisplay.printColor("Naming tomogram as: "+self.params['name'], "cyan")

		newtomopath = os.path.join(self.params['rundir'], self.params['name']+".mrc")
		print newtomopath
		origtomopath = self.params['file']
		if os.path.isfile(newtomopath):
			if self.checkExistingFile():
				return
		else:
			### simple upload, just copy file to Tomo folder
			apDisplay.printMsg("Copying original tomogram to a new location: "+newtomopath)
			shutil.copyfile(origtomopath, newtomopath)
			if self.params['image']:
				shutil.copyfile(self.params['image'], self.params['rundir']+'/snapshot.png')			

		### upload Initial Tomo
		self.params['projectId'] = apProject.getProjectIdFromSessionName(self.params['session'])
		
		### inserting tomogram
		apUpload.insertTomo(self.params)

#=====================
#=====================
if __name__ == '__main__':
	uploadTomo = UploadTomoScript()
	uploadTomo.start()
	uploadTomo.close()
