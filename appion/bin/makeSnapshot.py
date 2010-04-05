#!/usr/bin/env python
# Make structure snapshots using chimera

import os
import re
import glob
import shutil
#appion
from appionlib import appionScript
from appionlib import apChimera
from appionlib import apVolume
from appionlib import apDisplay
from appionlib import apFile
from pyami import mrc, imagefun

#=====================
#=====================
class MakeSnapshotScript(appionScript.AppionScript):
	#=====================
	def uploadScriptData(self):
		return

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<filename> --sym=<c1,icos,d7> \n\t "
			+" [--contour=<#>] [--zoom=<#>] [--type=<snapshot>] ")
		self.parser.add_option("-f", "--file", dest="file", 
			help="3d MRC file to snapshot", metavar="FILE")
		self.parser.add_option("--pdb", dest="pdb", 
			help="PDB file to include in snapshots", metavar="FILE")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.0,
			help="Zoom factor for snapshot rendering (1.0 by default)", metavar="#")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=2.0,
			help="Sigma level at which snapshot of density will be contoured (2.0 by default)", metavar="FLOAT")
		self.parser.add_option("-s", "--sym", "--symmetry", dest="sym", default='c1',
			help="Symmetry name, e.g. d7, c1, c4, or icos", metavar="")
		self.parser.add_option("-b", "--bin", dest="bin", type="int",
			help="Bin the volume before imaging", metavar="")

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

		### true/false
		self.parser.add_option("--xvfb", dest="xvfb", default=True,
			action="store_true", help="Use Xvfb for imaging")
		self.parser.add_option("--no-xvfb", dest="xvfb", default=True,
			action="store_false", help="Do not use Xvfb for imaging")
		self.parser.add_option("--no-silhouette", dest="silhouette", default=True,
			action="store_false", help="Do not use silhouettes for imaging")

	#=====================
	def checkConflicts(self):
		if self.params['file'] is None:
			apDisplay.printError("Enter a file name, e.g. -f threed.20a.mrc")
		if not os.path.isfile(self.params['file']):
			apDisplay.printError("File not found: "+self.params['file'])
		self.params['file'] = os.path.abspath(self.params['file'])
		if self.params['pdb'] is not None:
			if not os.path.isfile(self.params['pdb']):
				apDisplay.printError("File not found: "+self.params['pdb'])
			self.params['pdb'] = os.path.abspath(self.params['pdb'])
		self.params['commit'] = False
		if self.params['sym'] is None:
			apDisplay.printError("Enter a symmetry group, e.g. d7, c1, c4, or icos")
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
		### bin the volume
		if self.params['bin'] is not None and self.params['bin'] > 1:
			apDisplay.printMsg("Binning volume")
			newmrcfile = os.path.join(self.params['rundir'], "binned.mrc")
			voldata = mrc.read(mrcfile)
			voldata = imagefun.bin3(voldata, self.params['bin'])
			mrc.write(voldata, newmrcfile)
			del voldata
			self.params['apix'] *= self.params['bin']
			if os.path.isfile(newmrcfile):
				mrcfile = newmrcfile

		### scale by mass
		if self.params['mass'] is not None:
			apDisplay.printMsg("Using scale by mass method")
			newmrcfile = os.path.join(self.params['rundir'], "setmass.mrc")
			shutil.copy(self.params['file'], newmrcfile)
			apChimera.setVolumeMass(newmrcfile, apix=self.params['apix'], mass=self.params['mass'])
			self.params['contour'] = 1.0
			if os.path.isfile(newmrcfile):
				mrcfile = newmrcfile

		### print stats
		box = apVolume.getModelDimensions(mrcfile)
		apDisplay.printColor("Box: %d   Apix: %.2f   File: %s"%
			(box, self.params['apix'], os.path.basename(mrcfile)), "green")

		### animation
		if self.params['type'] != "snapshot":
			apDisplay.printMsg("Creating animation")
			apChimera.renderAnimation(mrcfile, contour=self.params['contour'],
				 zoom=self.params['zoom'], sym=self.params['sym'],
				 color=self.params['color'], xvfb=self.params['xvfb'],
				 name=self.params['file'], silhouette=self.params['silhouette'])

		### snapshot
		if self.params['type'] != "animate":
			apDisplay.printMsg("Creating snapshots")
			apChimera.renderSnapshots(mrcfile, contour=self.params['contour'],
				zoom=self.params['zoom'], sym=self.params['sym'],
				color=self.params['color'], xvfb=self.params['xvfb'],
				pdb=self.params['pdb'], name=self.params['file'],
				silhouette=self.params['silhouette'])

		### clean up
		if self.params['mass'] is not None or self.params['bin'] is not None:
			images = glob.glob(mrcfile+"*")
			for img in images:
				newimg = re.sub(mrcfile, self.params['file'], img)
				shutil.move(img, newimg)
			apFile.removeFile(mrcfile)


#=====================
#=====================
if __name__ == '__main__':
	makeSnap = MakeSnapshotScript()
	makeSnap.start()
	makeSnap.close()
