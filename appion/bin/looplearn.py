#!/usr/bin/env python

#pythonlib
import os
import numpy
import time
#appion
from appionlib import appionLoop2
from appionlib import apDisplay
from appionlib import apDDResult
from appionlib.apCtf import ctfdb
from leginon import leginondata
from leginon import ptolemyhandler as ph

class LoopLearner(appionLoop2.AppionLoop):
	'''
	This simple script just print the image filename. It can
	be used to test appionLoop and or simply propogate donedict.
	'''

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "learn"

	#======================
	def processImage(self, imgdata):
		if not imgdata['target']['ptolemy_hole']:
			apDisplay.printWarning('Not ptolemy active learning image')
			self.icedata = None
			self.ctfvalue = None
			return
		if imgdata['camera']['align frames']:
			dd = apDDResult.DDResults(imgdata)
			self.unaligned = dd.getAlignImagePairData()['source']
		else:
			self.unaligned = imgdata
		apDisplay.printMsg('processing %s' % (imgdata['filename']))
		self.icedata = self.getIceThicknessData(self.unaligned)
		ctfvalue, conf = ctfdb.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			apDisplay.printWarning('No ctf estimation, yet.  Wait until it exists')
			time.sleep(30)
			return self.processImage(imgdata)
		self.ctfvalue = ctfvalue

	def getIceThicknessData(self, imgdata):
		return leginondata.ObjIceThicknessData(image=imgdata).query(results=1)

	#======================
	def setupParserOptions(self):
		return

	#======================
	def checkConflicts(self):
		return

	#======================
	def commitToDatabase(self, imgdata):
		if not self.unaligned['target']['ptolemy_hole']:
			# Not valid to learn
			return
		# post ctf resolution and ice thickness to ptolemy
		ctf_res = min(self.ctfvalue['resolution_50_percent'], self.ctfvalue['ctffind4_resolution']) #Angstrom
		if not self.icedata:
			apDisplay.printError('need ice thickness from Objective Aperture measurement')
		thickness = self.icedata[0]['thickness']*1e9 #??? nm
		hole_ids = [self.unaligned['target']['ptolemy_hole']['hole_id'],]
		ctfs = [ctf_res,]
		ice_thicknesses = [thickness,]
		ph.visit_holes(hole_ids, ctfs, ice_thicknesses)
		apDisplay.printMsg('inserted %d visited holes in session %s' % (len(hole_ids), self.unaligned['session']['name']))
		# TODO: redo target ordering on square targets
		return

if __name__ == '__main__':
	testLoop = LoopLearner()
	testLoop.run()

