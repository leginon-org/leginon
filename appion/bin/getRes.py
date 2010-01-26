#!/usr/bin/env python

from appionlib import appionScript
from appionlib import apDisplay
import os
from appionlib import apRecon

class getResScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.quiet = True
		self.parser.set_usage("Usage: %prog --fscfile=FILE --boxsize=INT --apix=FLOAT")
		self.parser.add_option("-f", "--fscfile", dest="fscfile",
			help="FSC file from EMAN", metavar="FILE")
		self.parser.add_option("-b", "--boxsize", dest="boxsize", type="int",
			help="Box size in pixels", metavar="INT")
		self.parser.add_option("-a", "--apix", dest="apix", type="float",
			help="Angstroms per pixels", metavar="FLOAT")


	#=====================
	def checkConflicts(self):
		if self.params['fscfile'] is None:
			apDisplay.printError("fscfile was not defined")
		if not os.path.isfile(self.params['fscfile']):
			apDisplay.printError("fscfile "+self.params['fscfile']+" was not found")
		if self.params['boxsize'] is None:
			apDisplay.printError("Box size was not defined")
		if self.params['apix'] is None:
			apDisplay.printError("Angstroms per pixels was not defined")

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#=====================
	def start(self):
		res = apRecon.getResolutionFromFSCFile(self.params['fscfile'], self.params['boxsize'], self.params['apix'])
		apDisplay.printColor( ("resolution: %.5f" % (res)), "cyan")


#=====================
if __name__ == "__main__":
	getRes = getResScript()
	getRes.start()
	getRes.close()

