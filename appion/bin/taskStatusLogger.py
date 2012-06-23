#!/usr/bin/env python
import sys
import time
import subprocess
import math
from appionlib import basicScript
'''
taskStatusLogger examines an output file of a job task and output short status lines to sys.stdout
'''
class TaskStatusLogger(basicScript.BasicScriptInstanceRun):
	'''
	taskStatusLogger creates an instance of apTaskLog or its subclasses
	according to the jobtype
	'''
	def createInst(self, jobtype, command):
		jobInstance = None
		if "emanrecon" == jobtype:
			from appionlib import apTaskLogEman
			return apTaskLogEman.EmanTaskLog(command)
		elif "frealignrecon" == jobtype:
			from appionlib import apTaskLogFrealign
			return apTaskLogFrealign.FrealignTaskLog(command)
		elif "xmipprecon" == jobtype:
			from appionlib import apTaskLog
			return apTaskLog.TaskLog(command)
		elif "xmippml3drecon" == jobtype:
			from appionlib import apTaskLog
			return apTaskLog.TaskLog(command)
		else:
			from appionlib import apTaskLog
			return apTaskLog.TaskLog(command)

if __name__ == '__main__':
	testscript = TaskStatusLogger()
