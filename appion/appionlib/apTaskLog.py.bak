import sys
import time
import subprocess
import math
import os

from appionlib import basicScript
from appionlib import apParam
from appionlib import apDisplay

class TaskLog(basicScript.BasicScript):
	'''
	TaskLog is used by TaskStatusLogger.py
	on remote cluster host to parse the logfile or result of a task 
	for useful messages	and added to the logfile of the job
	so that appion can monitor it from the local webserver
	'''
	def __init__(self,optlist=[]):
		super(TaskLog,self).__init__(optlist,True)
		self.setAttributes()
		self.__checkTaskLogExistance()

	#=====================
	def setupParserOptions(self):
		# Agent class uses this to choose the RefineJob subclass
		self.parser.add_option("--jobtype", dest="jobtype",
			help="Job Type of processing run, e.g., emanrecon", metavar="X")
		self.parser.add_option("--tasktype", dest="tasktype",
			help="Type of task the logfile come from specific to the jobtype, e.g., 'refine' for emanrecon", metavar="X")
		self.parser.add_option("--iter", dest="iter", type="int", default=1,
			help="current iteration if applicable", metavar="INT")
		self.parser.add_option("--tasklogfile", dest="tasklogfile",
			help="Path for the task logfile. if relative path is given, current directory is assumed e.g. --tasklogfile=/home/you/sessionname/recon/runname/recon/refine1.log", metavar="PATH")
		
	#=====================
	def checkConflicts(self):
		if self.params['jobtype'] is None:
			apDisplay.printError("enter the refine jobtype, e.g. --jobtype=emanrecon")
		
	def setAttributes(self):
		self.jobtype = self.params['jobtype']
		self.tasktype = self.params['tasktype']
		self.tasklogfile = os.path.abspath(self.params['tasklogfile'])
		self.iter = self.params['iter']
		self.failed = False

	def __checkTaskLogExistance(self):
		tasktype_display = self.tasktype.upper()
		tasklog_basename = os.path.basename(self.tasklogfile)
		if not os.path.isfile(self.tasklogfile):
			self.failed = True
			apDisplay.printError('task %s did not produce %s' % (tasktype_display,tasklog_basename),raised=False)
		else:
			apDisplay.printMsg('task %s produced successfully file %s' % (tasktype_display,tasklog_basename))
			if os.stat(self.tasklogfile)[6] == 0:
				self.failed = True
				apDisplay.printError('task %s file %s is empty' % (tasktype_display,tasklog_basename),raised=False)

	def examineTaskLog(self):
		'''
		add other log testing here
		'''
		pass

	def start(self):
		# no need to examine tasklog content if already failed
		if not	self.failed:
			self.examineTaskLog()

if __name__ == '__main__':
	test = TaskLog()
	test.start()
	test.close()
