#!/usr/bin/env python
import os
import sys
import math
import time
#appion
from appionlib import apDisplay
from appionlib import apTaskLog

#================
#================
class EmanTaskLog(apTaskLog.TaskLog):
	def examineTaskLog(self):
		if self.tasktype == 'refine':
			self.checkRefineLogError()
		elif self.tasktype == 'make3d':
			self.checkReconVolume()
		elif self.tasktype == 'eotest':
			self.checkResolutionResult()

	def checkRefineLogError(self):
		f = open(self.tasklogfile)
		text = f.read()
		f.close()
		tasklog_basename = os.path.basename(self.tasklogfile)
		# check alarm and error
		if 'Alarm' in text:
			self.failed = True
			apDisplay.printError('There are Alarm Errors in %s' % (tasklog_basename),False)
		if 'Error' in text:
			self.failed = True
			apDisplay.printError('There are Unknown Errors in %s' % (tasklog_basename),False)

	def checkResolutionResult(self):
		f = open(self.tasklogfile)
		lines = f.readlines()
		f.close()
		if len(lines) != self.iter:
			self.failed = True
			apDisplay.printError('Resolution not determined up to iteration %d' %(self.iter,),False)
		else:
			apDisplay.printMsg('Resolution at iteration %d is %s A' % (self.iter,lines[-1][:-1]))

	def checkReconVolume(self):
		from pyami import mrc
		h = mrc.readHeaderFromFile(self.tasklogfile)
		if h['amax'] == h['amin']:
			apDisplay.printError('Reconstruction gives no real density.  Is the mask too tight? If not, consider using larger "hard" value to exclude fewer images in recostruction.',False)

if __name__ == '__main__':
	app = EmanTaskLog()
	app.start()
	app.close()
