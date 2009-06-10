#!/usr/bin/env python
# Make structure snapshots using chimera

import os
import re
import glob
import shutil
#appion
import appionScript
import apChimera
import apVolume
import apDisplay
import apFile

#=====================
#=====================
class MakeSnapshotScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<filename> --sym=<c1,icos,d7> \n\t "
			+" [--contour=<#>] [--zoom=<#>] [--type=<snapshot>] ")
		self.parser.add_option("-f", "--file", dest="file", 
			help="3d MRC file to snapshot", metavar="FILE")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.0,
			help="Zoom factor for snapshot rendering (1.0 by default)", metavar="#")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=2.0,
			help="Sigma level at which snapshot of density will be contoured (2.0 by default)", metavar="FLOAT")
		self.parser.add_option("-s", "--sym", "--symmetry", dest="sym", default='c1',
			help="Symmetry name, e.g. d7, c1, c4, or icos", metavar="")

		### mass
		self.parser.add_option("-m", "--mass", dest="mass", type="float",
			help="Mass in kDa of particle to set contouring", metavar="kDa")
		self.parser.add_option("-a", "--apix", dest="apix", type="float", default=1.0,
			help="Pixel size in Angstroms (only required for mass)", metavar="FLOAT")

		### strings
		self.parser.add_option("--color", dest="color",
			help="Override color choice", metavar="COLOR")

		### choices
		self.typemodes = ( "snapshot", "animate", "both" )
		self.parser.add_option("-t", "--type", dest="type",
			help="Snapshot mode: "+str(self.typemodes), metavar="TYPE", 
			type="choice", choices=self.typemodes, default="snapshot" )

	#=====================
	def checkConflicts(self):
		if self.params['sym'] is None:
			apDisplay.printError("Enter a symmetry group, e.g. d7, c1, c4, or icos")
		if self.params['file'] is None:
			apDisplay.printError("Enter a file name, e.g. -f threed.20a.mrc")
		if self.params['mass'] is not None and self.params['apix'] is None:
			apDisplay.printError("Please provide apix if using mass based threshold")

		if not os.path.isfile(self.params['file']):
			apDisplay.printError("Could not find file: "+self.params['file'])
		self.params['file'] = os.path.abspath(self.params['file'])

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#=====================
	def start(self):
		mrcfile = self.params['file']
		box = apVolume.getModelDimensions(mrcfile)
		apDisplay.printMsg("Box: %.2f Apix: %.2f for file %s"%
			(box, self.params['apix'], os.path.basename(mrcfile)))
	
		### scale by mass
		if self.params['mass'] is not None:
			apDisplay.printMsg("Using scale by mass method")
			mrcfile = os.path.join(self.params['rundir'], "temp.mrc")
			shutil.copy(self.params['file'], mrcfile)
			apChimera.setVolumeMass(mrcfile, apix=self.params['apix'], mass=self.params['mass'])
			self.params['contour'] = 1.0

		### snapshot
		if self.params['type'] != "snapshot":
			apDisplay.printMsg("Creating animation")
			apChimera.renderAnimation(mrcfile, contour=self.params['contour'],
				 zoom=self.params['zoom'], sym=self.params['sym'],
				 color=self.params['color'])

		### animation
		if self.params['type'] != "animate":
			apDisplay.printMsg("Creating snapshots")
			apChimera.renderSnapshots(mrcfile, contour=self.params['contour'],
				 zoom=self.params['zoom'], sym=self.params['sym'],
				 color=self.params['color'])

		### clean up
		if self.params['mass'] is not None:
			images = glob.glob(mrcfile+"*")
			for img in images:
				newimg = re.sub(mrcfile, self.params['file'], img)
				shutil.move(img, newimg)
			apFile.removeFile("temp.mrc")

#=====================
#=====================
if __name__ == '__main__':
	makeSnap = MakeSnapshotScript()
	makeSnap.start()
	makeSnap.close()
