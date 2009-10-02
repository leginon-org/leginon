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
		self.parser.add_option("--transform", dest="transform", 
			help="method for transforming YZ to standard order (e.g. rotx or flipyz)")
		self.parser.add_option("-v", "--volume", dest="volume",
			help="Subvolume from original voxel volume", default='', metavar="VOLUME")
		self.parser.add_option("-b", "--bin", dest="bin", type="int",
			help="Extra Binning from tiltseries image", default=1, metavar="#")
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert tomogram density")

	#=====================
	def checkConflicts(self):
		if self.params['rundir']:
			# use the same directory for alignment file if rundir is specified
			self.params['aligndir'] = self.params['rundir']
		if self.params['tiltseriesnumber'] is None:
			apDisplay.printError("Enter a Tilt Series")
		if self.params['transform']:
			#remove whitespaces
			self.params['transform'] = self.params['transform'].split()[-1]
		if not self.params['volume']:
			self.params['full'] = True
			if not self.params['order']:
				self.params['order'] = 'XZY'
			if self.params['order'] != 'XYZ' and self.params['order'] != 'XZY':
				if self.params['transform']:
					apDisplay.printError("Only transformations from XYZ or XZY are implemented")
		else:
			self.params['full'] = False
			if not self.params['order']:
				self.params['order'] = 'XYZ'
			if self.params['order'] != 'XZY' and self.params['order'] != 'XYZ':
				if self.params['transform']:
					apDisplay.printError("Only transformations from XZY are implemented")
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
		self.params['aligndir'] = os.path.abspath(os.path.join(path,tiltseriespath,'align',self.params['runname']))

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
	def getOriginalVolumeShape(self):
		origtomopath = self.params['file']
		self.origheader = mrc.readHeaderFromFile(origtomopath)
		self.origshape = self.origheader['shape']

	def getImageShapeFromTiltSeries(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(self.params['tiltseriesnumber'],sessiondata)
		firstimagedata = apTomo.getFirstImage(tiltdata)
		self.imageshape = apTomo.getTomoImageShape(firstimagedata)
	#=====================
	def checkExistingFile(self):
		savedtomopath = os.path.join(self.params['rundir'], self.params['name']+".rec")
		origtomopath = self.params['file']
		apDisplay.printWarning("A Tomogram by the same filename already exists: '"+savedtomopath+"'")
		### a tomogram by the same name already exists
		savedheader = mrc.readHeaderFromFile(savedtomopath)
		savedshape = savedheader['shape']
		origheader = self.origheader
		origshape = self.origshape
		order = self.params['order']
		if self.params['full']:
			newshape = (self.imageshape[0], origshape[order.find('Z')], self.imageshape[1])
		else:
			newshape = (origshape[order.find('X')], origshape[order.find('Y')], origshape[order.find('Z')])
		# not using md5 for file comparison because it takes too long.  With padding, only min and max are stable
		if newshape != savedshape or savedheader['amax'] != origheader['amax'] or savedheader['amin'] != origheader['amin']:
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
			apDisplay.printWarning("Upload Not Allowed")
			self.params['commit'] = False
			return True
		else:
			### they are the same, but it is not in the database
			apDisplay.printWarning("The same tomogram with name '"+savedtomopath+"' already exists, but is not uploaded!")
			if self.params['commit'] is True:
				apDisplay.printMsg("Inserting tomogram into database...")

	#=====================
	def start(self):
		cleanlist = []
		# imod needs the recon files named as .rec  It may need some fix later
		if self.params['name'] is None:
			self.setNewFileName()
		apDisplay.printColor("Naming tomogram as: "+self.params['name'], "cyan")
		newtomopath = os.path.join(self.params['rundir'], self.params['name']+".rec")
		origtomopath = self.params['file']
		origxfpath = self.params['oldxffile']
		apParam.createDirectory(self.params['aligndir'])
		newxfpath = os.path.join(self.params['aligndir'], self.params['newxffile'])
		order = self.params['order']
		voltransform = self.params['transform']
		bin = self.params['bin']
		self.getImageShapeFromTiltSeries()
		self.getOriginalVolumeShape()
		if os.path.isfile(newtomopath):
			uploaded_before = self.checkExistingFile()
			if uploaded_before:
				return
		else:
			currenttomopath = origtomopath
			if self.params['full']:
				### full tomogram upload, may need to pad to the image size
				if self.params['order'] == 'XZY' and not voltransform:
					apDisplay.printMsg("Default full tomogram orientation with original handness")
				else:
					if voltransform:
						apDisplay.printMsg("Transforming original tomogram....")
						currenttomopath = apImod.transformVolume(origtomopath,voltransform)
						cleanlist.append(currenttomopath)
				### padding the XZY tomogram to the image size
				currentheader = mrc.readHeaderFromFile(currenttomopath)
				currentshape = currentheader['shape']
				currentxyshape = currentshape[0], currentshape[2]
				imageshape = self.imageshape
				print imageshape, currentxyshape
				if currentxyshape[0] < imageshape[0]/bin or currentxyshape[1] < imageshape[1]/bin:
					currenttomopath = apImod.pad(currenttomopath,currentxyshape,imageshape,bin,'XZY')
					cleanlist.append(currenttomopath)
			else:
				### subtomogram simple upload, just copy file to Tomo folder
				if self.params['order'] == 'XYZ' and not voltransform:
					apDisplay.printMsg("Default sub tomogram orientation")
				else:
					if voltransform:
						apDisplay.printMsg("Transforming original tomogram....")
						currenttomopath = apImod.transformVolume(origtomopath,voltransform)
						cleanlist.append(currenttomopath)
			### simple upload, just copy file to Tomo folder
			apDisplay.printMsg("Copying original tomogram to a new location: "+newtomopath)
			shutil.copyfile(currenttomopath, newtomopath)
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
			self.params['zprojfile'] = apImod.projectFullZ(self.params['rundir'], self.params['runname'], seriesname,bin,True,False)
		else:
			apTomo.makeMovie(newtomopath)
			apTomo.makeProjection(newtomopath)
		apTomo.uploadTomo(self.params)
		### clean up
		for tmpfilepath in cleanlist:
			apFile.removeFile(tmpfilepath)

#=====================
#=====================
if __name__ == '__main__':
	uploadTomo = UploadTomoScript()
	uploadTomo.start()
	uploadTomo.close()
