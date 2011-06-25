#!/usr/bin/env python
import sys
import time
import subprocess
import math

from appionlib import basicScript
from appionlib import apParam
from appionlib import apRefineJob
from appionlib import apRefineJobEman
from appionlib import apRefineJobFrealign

class RefineRunner(object):
	def __init__(self):
		self.jobtype = 'emanrecon'

		self.setJob()
		if self.job.setuponly:
			self.printCommands()

	def setJob(self):
		if self.jobtype is None:
			self.job = apRefineJob.Tester()
		elif self.jobtype.lower() == 'emanrecon':
			self.job = apRefineJobEman.EmanRefineJob()
		elif self.jobtype.lower() == 'frealignrecon':
			self.job = apRefineJobFrealign.FrealignRefineJob()

	def printCommands(self):
		print ''
		print '============JOB COMMANDS============'
		print ''
		for command in self.job.command_list:
			print command


if __name__ == '__main__':
	testscript = RefineRunner()
