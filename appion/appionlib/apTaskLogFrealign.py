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
class FrealignTaskLog(apTaskLog.TaskLog):
	def examineTaskLog(self):
		self.task_noun = ''
		if self.tasktype == 'refine':
			self.task_noun = 'refinement'
			self.checkRefineLogError()
		if self.tasktype == 'recon':
			self.task_noun = 'reconstruction'
			self.checkRefineLogError()
		elif self.tasktype == 'eotest':
			self.checkResolutionResult()

	def checkRefineLogError(self):
		f = open(self.tasklogfile)
		text = f.read()
		f.close()
		lines = text.split('\n')
		f.close()
		tasklog_basename = os.path.basename(self.tasklogfile)
		# check alarm and error
		if 'ERROR' in text:
			self.failed = True
			apDisplay.printError('There are Errors in %s' % (tasklog_basename),False)
		if 'WARNING' in text:
			apDisplay.printWarning('There are Warning in %s during %s' % (tasklog_basename,self.task_noun))
			for line in lines:
				if 'WARNING' in line:
					apDisplay.printWarning(line)


	def checkResolutionResult(self):
		f = open(self.tasklogfile)
		lines = f.readlines()
		f.close()
		if len(lines) != self.iter:
			self.failed = True
			apDisplay.printError('Resolution not determined up to iteration %d' %(self.iter,),False)
		else:
			apDisplay.printMsg('Resolution at iteration %d is %s A' % (self.iter,lines[-1][:-1]))

if __name__ == '__main__':
	app = FrealignTaskLog()
	app.start()
	app.close()
