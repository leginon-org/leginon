#!/usr/bin/env python

import os
import sys
from appionlib import apRecon
from appionlib import apDisplay
from appionlib import basicScript

class getResScript(basicScript.BasicScript):

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
		self.parser.add_option("-c", "--criteria", dest="criteria", type="float",
			help="FSC resolution criteria", metavar="FLOAT", default=0.5)

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
		res = apRecon.getResolutionFromFSCFile(self.params['fscfile'], 
			self.params['boxsize'], self.params['apix'], self.params['criteria'])
		apDisplay.printColor( ("resolution: %.5f at criteria %.3f" % (res, self.params['criteria'])), "cyan")
		sys.stdout.write("%s resolution %.5f (%.3f)\n"%(self.params['fscfile'], res, self.params['criteria']))

#=====================
if __name__ == "__main__":
	getRes = getResScript()
	getRes.start()
	getRes.close()

