#!/usr/bin/env python
import sys
import time
import subprocess
import math

'''
taskStatusLogger examines an output file of a job task and output short status lines to sys.stdout
'''
class taskStatusLogger(object):
	'''
	taskStatusLogger creates an instance of apTaskLog or its subclasses
	according to the jobtype
	'''
	def __init__(self):
		command = sys.argv[1:]
		jobtype = self.getJobType(command)
		statuslog = self.createLoggerInst(jobtype,command)
		statuslog.start()
		statuslog.close()

	def getJobType(self, command):
		jobtype = None

		#Search for the command option that specified the job type
		for option in command:
			if option.startswith(r'--jobtype='):
				#We only need the part after the '='
				jobtype = option.split('=')[1]
				#Don't process anymore of the list then needed
				break

		return jobtype

	def createLoggerInst(self, jobType, command):
		jobInstance = None
		if "emanrecon" == jobType:
			from appionlib import apTaskLogEman
			jobInstance = apTaskLogEman.EmanTaskLog(command)
		elif "frealignrecon" == jobType:
			from appionlib import apTaskLog
			jobInstance = apTaskLog.TaskLog(command)
		elif "xmipprecon" == jobType:
			from appionlib import apTaskLog
			jobInstance = apTaskLog.TaskLog(command)
		elif "xmippml3drecon" == jobType:
			from appionlib import apTaskLog
			jobInstance = apTaskLog.TaskLog(command)
		else:
			from appionlib import apTaskLog
			jobInstance = apTaskLog.TaskLog(command)
		return jobInstance

if __name__ == '__main__':
	testscript = taskStatusLogger()
