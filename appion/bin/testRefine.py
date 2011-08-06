#!/usr/bin/env python
import sys
import time
import subprocess
import math
from appionlib import basicScript

class RefineTester(basicScript.BasicScriptInstanceRun):
	def createInst(self, jobtype, optargs):
		if jobtype is None:
			from appionlib import apRefineJob
			return apRefineJob.Tester(optargs)
		elif jobtype.lower() == 'emanrecon':
			from appionlib import apRefineJobEman
			return apRefineJobEman.EmanRefineJob(optargs)
		elif jobtype.lower() == 'frealignrecon':
			from appionlib import apRefineJobFrealign
			return apRefineJobFrealign.FrealignRefineJob(optargs)
		elif jobtype.lower() == 'xmipprecon':
			from appionlib import apRefineJobXmipp
			return apRefineJobXmipp.XmippSingleModelRefineJob(optargs)
		elif self.jobtype.lower() == 'xmippml3d':
			from appionlib import apRefineJobXmippML3d
			return apRefineJobXmippML3d.XmippML3dRefineJob(optargs)

	def printCommands(self):
		print ''
		print '============JOB COMMANDS============'
		print ''
		for command in self.app.command_list:
			print command

	def run(self):
		self.printCommands()

if __name__ == '__main__':
	test = RefineTester()
