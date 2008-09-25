#!/usr/bin/env python
# Make structure snapshots using chimera

import os
import appionScript
import apParam
import apRecon
import apDisplay

#=====================
#=====================
class MakeSnapshotScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog --file=<filename> --sym=<#> \n\t "
			+" [--contour=<#>] [--zoom=<#>] ")

		self.parser.add_option("-f", "--file", dest="file", 
			help="3d MRC file to snapshot", metavar="FILE")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to store snapshots (default=current dir)", metavar="PATH")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.5,
			help="Zoom factor for snapshot rendering (1.5 by default)", metavar="#")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=2.0,
			help="Sigma level at which snapshot of density will be contoured (2.0 by default)", metavar="FLOAT")
		self.parser.add_option("-s", "--sym", "--symmetry", dest="sym",
			help="Symmetry name, e.g. d7, c1, c4, or icos", metavar="")


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
	def setOutDir(self):
		self.params['outdir'] = os.getcwd()

	#=====================
	def start(self):
		### set the environment parameters
		chimsnapenv = ( "%s,%s,%s,%.3f,%.3f" % (
			self.params['file'], 
			self.params['file'], 
			self.params['sym'], 
			self.params['contour'], 
			self.params['zoom'], ))
		os.environ["CHIMENV"] = chimsnapenv

		### run the script
		appiondir = apParam.getAppionDirectory()
		chimsnappath = os.path.join(appiondir, "bin", "apChimSnapshot.py")
		apRecon.runChimeraScript(chimsnappath)


#=====================
#=====================
if __name__ == '__main__':
	makeSnap = MakeSnapshotScript()
	makeSnap.start()
	makeSnap.close()
