#!/usr/bin/env python

import os
from appionlib import apDisplay
from appionlib import filterLoop

#This program is used by Topaz to PreProcess Images

#=====================
#=====================
#=====================
class MiniFilterLoop(filterLoop.FilterLoop):
	def setupParserOptions(self):
		#uses all the default values :)
		return
	def checkConflicts(self):
		#uses all the default values :)
		return
	def commitToDatabase(self, imgdata):
		#do nothing
		return
	def processImage(self, imgdict, filtarray):
		return

#=====================
#=====================
if __name__ == '__main__':
	preprocessor = MiniFilterLoop()
	preprocessor.run()
	preprocessor.close()