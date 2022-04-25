#!/usr/bin/env python

#python
import os
import shutil
import random
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apStackFormat

class convertStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.formatoptions = ("eman", "spider", "frealign", "xmipp")
		self.parser.set_usage("Usage: %prog --stackid=ID --format=PROGRAM_NAME [options]")
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("--format", dest="format", 
			default="spider", type="choice", choices=self.formatoptions,
			help="Format to be converted to, options: "+str(self.formatoptions))

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new runname was not defined")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		#new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		apStackFormat.linkFormattedStack(stackdata, self.params['format'],'test')
		#apStackFormat.replaceFormattedStack(stackdata, self.params['format'], self.params['rundir'],'normlist.doc')
		

#=====================
if __name__ == "__main__":
	subStack = convertStackScript()
	subStack.start()
	subStack.close()

