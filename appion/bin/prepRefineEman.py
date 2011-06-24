#!/usr/bin/env python

#python
import os
import shutil
import time
import math
#appion
from appionlib import appionScript
from appionlib import appiondata
from leginon import leginondata
from appionlib import apPrepRefine
from appionlib import apFile
from appionlib import apModel
from appionlib import apVolume
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apInstrument

class EmanPrep3DRefinement(apPrepRefine.Prep3DRefinement):
	def onInit(self):
		self.refinemethod = 'eman'
		self.files_to_send = []

	def setFormat(self):
		self.spidersingle = False

	def setFilesToSend(self):
		self.files_to_send.extend([self.model['file'],self.stack['file'],self.stack['file'].replace('hed','img')])

#=====================
if __name__ == "__main__":
	app = EmanPrep3DRefinement()
	app.start()
	app.close()

