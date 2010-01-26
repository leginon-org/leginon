#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import sys
import shutil
import re
#leginon
import leginondata
#appion
from appionlib import appionScript

from appionlib import apTomo
from appionlib import apImod
from appionlib import apImage
from appionlib import apParam
from appionlib import apRecon
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apDatabase
from appionlib import apParticle

#=====================
#=====================
class tomoMovieMaker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tomoId=<id> --rundir=<dir> "
			+"[options]")
		self.parser.add_option("--tomoId", dest="tomoId", type="int",
			help="tomogram id, e.g. --tomoId=2", metavar="int")
		self.parser.add_option("--maxsize", dest="maxsize", type="int",
			help="Maximum movie pixel numbers in x or y, whichever is larger. Will respect proportion in scaling, e.g. --maxsize=500", default = 512, metavar="int")

		return 

	#=====================
	def checkConflicts(self):
			if self.params['tomoId'] is None:
				apDisplay.printError("enter a tomogram id, e.g. --tomoId=2")
			if self.params['rundir'] is not None:
				self.tomodata = apTomo.getTomogramData(self.params['tomoId'])
				if self.params['rundir'] != self.tomodata['path']['path']:
					apDisplay.printError("The movie should only be put in the same path as the tomogram")

	def setRunDir(self):
		self.tomodata = apTomo.getTomogramData(self.params['tomoId'])
		self.params['rundir'] = self.tomodata['path']['path']

	def checkRequiredPrograms(self):
		exenames = ['3dmod','mencoder']
		for exname in exnames:
			exefile = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(exefile):
			apDisplay.printError(exename+" was not found in the path")

	def start(self):
		tomogram = self.params['rundir']+'/'+self.tomodata['name']+'.rec'
		if not os.path.isfile(tomogram):
			tomogram = self.params['rundir']+'/'+self.tomodata['name']+'.mrc'
			if not os.path.isfile(tomogram):
					apDisplay.printError("tomogram not exist")
		apTomo.makeMovie(tomogram,self.params['maxsize'])
		apTomo.makeProjection(tomogram,self.params['maxsize'])
				
			
#=====================
#=====================
if __name__ == '__main__':
	app = tomoMovieMaker()
	app.start()
	app.close()

	
