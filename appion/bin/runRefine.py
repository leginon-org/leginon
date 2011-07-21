#!/usr/bin/env python
import sys
import time
import subprocess
import math


class RefineRunner(object):
	def __init__(self):
		self.jobtype = 'emanrecon'
		optargs = sys.argv[1:]

		self.setJob(optargs)
		if self.job.setuponly:
			self.printCommands()

	def setJob(self,optargs):
		if self.jobtype is None:
			from appionlib import apRefineJob
			self.job = apRefineJob.Tester(optargs)
		elif self.jobtype.lower() == 'emanrecon':
			from appionlib import apRefineJobEman
			self.job = apRefineJobEman.EmanRefineJob(optargs)
		elif self.jobtype.lower() == 'frealignrecon':
			from appionlib import apRefineJobFrealign
			self.job = apRefineJobFrealign.FrealignRefineJob(optargs)
		elif self.jobtype.lower() == 'xmipprecon':
			from appionlib import apRefineJobXmipp
			self.job = apRefineJobXmipp.XmippSingleModelRefineJob(optargs)
		elif self.jobtype.lower() == 'xmippml3d':
			from appionlib import apRefineJobXmippML3d
			self.job = apRefineJobXmippML3d.XmippML3dRefineJob(optargs)

	def printCommands(self):
		print ''
		print '============JOB COMMANDS============'
		print ''
		for command in self.job.command_list:
			print command


if __name__ == '__main__':
	testscript = RefineRunner()
