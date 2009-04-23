#!/usr/bin/env python
# Upload tomograms to the database

import os
import sys
import time
import re
import shutil
from pyami import mrc
import appionScript
import apParam
import apFile
import apDisplay
import apDatabase
import apImod
import apTomo
#=====================
#=====================
class UploadTomoScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<filename> --session=<name> --symm=<#> \n\t "
			+" --res=<#> --description='text' [--contour=<#>] [--zoom=<#>] \n\t "
			+" [--rescale=<model ID,scale factor> --bin=<#>] ")
		self.parser.add_option("-i", "--image", dest="image",
			help="snapshot image file to upload", metavar="IMAGE")
		self.parser.add_option("-f", "--file", dest="file",
			help="MRC file to upload", metavar="FILE")
		self.parser.add_option("--xffile", dest="oldxffile",
			help="global alignment file to upload", metavar="FILE")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--name", dest="name",
			help="File name for new tomogram, automatically set")
		self.parser.add_option("-t", "--tiltseries", dest="tiltseriesnumber", type="int",
			help="Tilt Series # for a given session, Manually specified", metavar="TILTSERIES")
		self.parser.add_option("--order", dest="order", 
			help="Axis order (e.g. XZY where XY is the untilted image column and row)")
		self.parser.add_option("-v", "--volume", dest="volume",
			help="Subvolume from original voxel volume", default='', metavar="VOLUME")
		self.parser.add_option("-b", "--bin", dest="bin", type="int",
			help="Extra Binning from tiltseries image", default=1, metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['tiltseriesnumber'] is None:
			apDisplay.printError("Enter a Tilt Series")
		if not self.params['volume']:
			self.params['full'] = True
			if not self.params['order']:
				self.params['order'] = 'XZY'
			if self.params['oldxffile'] is None:
				apDisplay.printWarning("Subvolume boxing not possible without alignment file uploading")
		else:
			self.params['full'] = False
			if not self.params['order']:
				self.params['order'] = 'XYZ'
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['description'] is None:
			apDisplay.printError("Enter a description of the initial model")
		elif self.params['file'] is not None:
			if not os.path.isfile(self.params['file']):
				apDisplay.printError("could not find file: "+self.params['file'])
			self.params['file'] = os.path.abspath(self.params['file'])
		else:
			apDisplay.printError("Please provide a tomogram .mrc to upload")

	#=====================
	def setRunDir(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("/leginon/","/appion/",path)
		path = re.sub("/rawdata","/tomo",path)
		tiltseriespath = "tiltseries%d" % self.params['tiltseriesnumber']
		if self.params['full']:
			tomovolumepath = ""
		else:
			tomovolumepath = self.params['volume']
		intermediatepath = os.path.join(tiltseriespath,self.params['runname'],tomovolumepath)
		self.params['rundir'] = os.path.join(path,intermediatepath)

	#=====================
	def setNewFileName(self, unique=False):
		# set name to be like tomomaker
		seriesname = "%s_%03d" % (self.params['session'],self.params['tiltseriesnumber'])
		if self.params['full']:
			reconname = seriesname+"_full"
		else:
			reconname = seriesname+"_"+self.params['volume']
		self.params['name'] = reconname
		self.params['newxffile'] = seriesname+".xf"
		
		#clean up old name
		if self.params['image']:
			snapshotname = os.path.basename(self.params['image'])
			snapshotname = re.sub(".png", "", snapshotname)

	#=====================
	def checkExistingFile(self):
		savedtomopath = os.path.join(self.params['rundir'], self.params['name']+".rec")
		origtomopath = self.params['file']
		apDisplay.printWarning("A Tomogram by the same filename already exists: '"+newtomopath+"'")
		### a tomogram by the same name already exists
		savedheader = mrc.readHeaderFromFile(savedtomopath)
		savedshape = savedheader['shape']
		origheader = mrc.readHeaderFromFile(origtomopath)
		origshape = origheader['shape']
		order = self.params['order']
		if self.params['full']:
			newshape = (origshape(order.find('X')), origshape(order.find('Z')), origshape(order.find('Y')))
		else:
			newshape = (origshape(order.find('X')), origshape(order.find('Y')), origshape(order.find('Z')))
		if newshape != savedshape or savedheader['amax'] != origheader['amax'] or savedheader['amin'] != origheader['amax'] or savedheader['amean'] != origheader['amean']:
			different = True
		else:
			different = False
			mdnew = None
		if different:
			apDisplay.printWarning("The tomograms are different, cannot overwrite")
			return True
		elif apDatabase.isTomoInDB(mdnew,self.params['full'],savedtomopath):
			### they are the same and its in the database already
			apDisplay.printWarning("Identical Tomogram already exists in the database!")
			self.params['commit'] = False
			return True
		else:
			### they are the same, but it is not in the database
			apDisplay.printWarning("The same tomogram with name '"+savedtomopath+"' already exists, but is not uploaded!")
			if self.params['commit'] is True:
				apDisplay.printMsg("Inserting tomogram into database...")

	#=====================
	def start(self):
		# imod needs the recon files named as .rec  It may need some fix later
		if self.params['name'] is None:
			self.setNewFileName()
		apDisplay.printColor("Naming tomogram as: "+self.params['name'], "cyan")
		newtomopath = os.path.join(self.params['rundir'], self.params['name']+".rec")
		origtomopath = self.params['file']
		origxfpath = self.params['oldxffile']
		newxfpath = os.path.join(self.params['rundir'], self.params['newxffile'])
		if os.path.isfile(newtomopath):
			if self.checkExistingFile():
				return
		else:
			if self.params['full']:
				if self.params['order'] == 'XZY':
					apDisplay.printMsg("Default full tomogram orientation")
				elif self.params['order'] == 'XYZ':
					apDisplay.printMsg("Rotating original tomogram....")
					origtomopath = apImod.rotateVolume(origtomopath)
				else:
					apDisplay.printMsg("Not sure how to rotate/flip this....")
					return
			### simple upload, just copy file to Tomo folder
			else:
				if self.params['order'] == 'XYZ':
					apDisplay.printMsg("Default sub tomogram orientation")
				elif self.params['order'] == 'XZY':
					apDisplay.printMsg("Rotating original tomogram....")
					origtomopath = apImod.rotateVolume(origtomopath)
				else:
					apDisplay.printMsg("Not sure how to rotate/flip this....")
					return
			### simple upload, just copy file to Tomo folder
			apDisplay.printMsg("Copying original tomogram to a new location: "+newtomopath)
			shutil.copyfile(origtomopath, newtomopath)
			if origxfpath and os.path.isfile(origxfpath):
				apDisplay.printMsg("Copying original alignment to a new location: "+newxfpath)
				shutil.copyfile(origxfpath, newxfpath)
			if self.params['image']:
				shutil.copyfile(self.params['image'], self.params['rundir']+'/snapshot.png')
		### inserting tomogram
		tomoheader = mrc.readHeaderFromFile(newtomopath)
		self.params['shape'] = tomoheader['shape']
		if self.params['full']:
			seriesname = "%s_%03d" % (self.params['session'],self.params['tiltseriesnumber'])
			self.params['zprojfile'] = apImod.projectFullZ(self.params['rundir'], self.params['runname'], seriesname,True)
		else:
			apTomo.makeMovie(newtomopath)
			apTomo.makeProjection(newtomopath)
		apTomo.insertTomo(self.params)

#=====================
#=====================
if __name__ == '__main__':
	uploadTomo = UploadTomoScript()
	uploadTomo.start()
	uploadTomo.close()
