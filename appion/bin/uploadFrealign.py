#!/usr/bin/env python

#python
import os
import re
import sys
import time
import math
#appion
from appionlib import appionScript

class UploadFrealign(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --commit --description='<text>' [options]")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")

	#=====================
	def checkConflicts(self):
		apDisplay.printMsg("Conflicts")

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#=====================
	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		apDisplay.printMsg("Hey this works")

if __name__ == '__main__':
	upfrealign = UploadFrealign()
	upfrealign.start()
	upfrealign.close()
