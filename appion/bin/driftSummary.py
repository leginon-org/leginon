#!/usr/bin/env python

#pythonlib
import os
import numpy
#appion
from appionlib import appionLoop2
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay

class TestLoop(appionLoop2.AppionLoop):
	#=======================
	def preLoopFunctions(self):
			apDisplay.printMsg('DD Stack Processing')
			self.dd = apDDprocess.DDStackProcessing()
			self.summaryfile = 'maxdrift.txt'
			f = open(self.summaryfile,'w')
			f.write('filename\tmax drift(angstroms)\n')
			f.close()
			self.max_shift = None

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "drift"

	#======================
	def processImage(self, imgdata):
		if imgdata is None or imgdata['camera']['save frames'] != True:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return
		# find the ddstackrun of the image
		self.dd.setDDStackRun(self.params['ddstack'])
		self.dd.setImageData(imgdata)
		self.framelist = self.dd.getFrameList(self.params)
		# compare image ddstackrun with the specified ddstackrun
		if self.params['ddstack'] and self.params['ddstack'] != self.dd.getDDStackRun().dbid:
			apDisplay.printWarning('ddstack image not from specified ddstack run')
			apDisplay.printWarning('Skipping this image ....')
			return None
		# This function will reset self.dd.ddstackrun for actual processing
		self.dd.setFrameStackPath(self.params['ddstack'])

		shifts = self.dd.getShiftsBetweenFrames()
		self.max_shift = self.getLargestDrift(shifts)
		apDisplay.printMsg('Max shift : %.3f pixels' % (self.max_shift,))

	def saveValue(self,imgdata, value):
		f = open(self.summaryfile,'a')
		f.write('%s\t%.2f\n' % (imgdata['filename'], value))
		f.close()

	def getLargestDrift(self,shifts):
		return max(shifts)

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--ddstack", dest="ddstack", type="int", default=0,
			help="gain/dark corrected ddstack id used for dd frame integration")
		return

	#======================
	def checkConflicts(self):
		return

	#======================
	def commitToDatabase(self, imgdata):
		apix = apDatabase.getPixelSize(imgdata)
		angstrom_drift = self.max_shift * apix
		self.saveValue(imgdata,angstrom_drift)
		return

if __name__ == '__main__':
	powerLoop = TestLoop()
	powerLoop.run()

