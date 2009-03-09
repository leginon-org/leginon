#!/usr/bin/env python
# Make structure snapshots using chimera

import os
import appionScript
import apChimera
import apVolume
import apDisplay

#=====================
#=====================
class MakeSnapshotScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<filename> --sym=<c1,icos,d7> \n\t "
			+" [--contour=<#>] [--zoom=<#>] [--type=<snapshot>] ")
		self.parser.add_option("-f", "--file", dest="file", 
			help="3d MRC file to snapshot", metavar="FILE")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.5,
			help="Zoom factor for snapshot rendering (1.5 by default)", metavar="#")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=2.0,
			help="Sigma level at which snapshot of density will be contoured (2.0 by default)", metavar="FLOAT")
		self.parser.add_option("-s", "--sym", "--symmetry", dest="sym", default='c1',
			help="Symmetry name, e.g. d7, c1, c4, or icos", metavar="")

		### choices
		self.typemodes = ( "snapshot", "animate", "both" )
		self.parser.add_option("-t", "--type", dest="type",
			help="Snapshot mode: "+str(self.typemodes), metavar="MODE", 
			type="choice", choices=self.typemodes, default="snapshot" )

	#=====================
	def checkConflicts(self):
		if self.params['sym'] is None:
			apDisplay.printError("Enter a symmetry group, e.g. d7, c1, c4, or icos")
		if self.params['file'] is None:
			apDisplay.printError("Enter a file name, e.g. -f threed.20a.mrc")
		if not os.path.isfile(self.params['file']):
			apDisplay.printError("Could not find file: "+self.params['file'])
		self.params['file'] = os.path.abspath(self.params['file'])

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#=====================
	def start(self):
		box = apVolume.getModelDimensions(self.params['file'])
		if self.params['type'] != "snapshot":
			apDisplay.printMsg("Creating animation")
			apChimera.renderAnimation(self.params['file'], res=30, contour=self.params['contour'], zoom=self.params['zoom'],
				apix=None, sym=self.params['sym'], box=box, lpfilter=False)
		if self.params['type'] != "animate":
			apDisplay.printMsg("Creating snapshots")
			apChimera.renderSnapshots(self.params['file'], res=30, contour=self.params['contour'], zoom=self.params['zoom'],
				apix=None, sym=self.params['sym'], box=box, lpfilter=False)

#=====================
#=====================
if __name__ == '__main__':
	makeSnap = MakeSnapshotScript()
	makeSnap.start()
	makeSnap.close()
