import os
import time
from appionlib import basicAgent
from appionlib import apDisplay

class ParallelTaskMonitor(basicAgent.BasicAgent):
	'''
	Monitor submitted parallel task by checking their job status.
	This makes the shell script to wait until the tasks are all done
	before performing the next task.
	'''
	def __init__(self,configFile=None,rundir='./'):
		super(ParallelTaskMonitor,self).__init__(configFile)
		self.taskjobids = []
		self.taskid_file = os.path.join(os.path.abspath(rundir),'task_jobids.save')
		self.checkStatusInterval = 2

	def getTaskJobIds(self):
		f = open(self.taskid_file)
		lines = f.readlines()
		f.close()
		self.taskjobids = map((lambda x: int(x)),lines)
		self.unfinished_task_status = {}
		for hostJobId in self.taskjobids:
			self.unfinished_task_status[hostJobId] = 'Q'

	def Main(self):
		if not os.path.isfile(self.taskid_file):
			apDisplay.printError('Missing %s for parallel task monitoring' % self.taskid_file)
		self.processingHost = self.createProcessingHost()
		self.getTaskJobIds()
		# wait until all done
		while len(self.unfinished_task_status):
			time.sleep(self.checkStatusInterval)
			for hostJobId in self.unfinished_task_status.keys():
				currentStatus = self.unfinished_task_status[hostJobId]
				newStatus = self.processingHost.checkJobStatus(hostJobId)
				if newStatus == "U" and (currentStatus == "R" or currentStatus == "Q"):
					newStatus = 'D'
				if newStatus == 'D':
					del self.unfinished_task_status[hostJobId]
		# reset
		os.remove(self.taskid_file)

if __name__ == "__main__":
	configfile = '/home/acheng/.appion.cfg'
	a = ParallelTaskMonitor(configfile,'./')
	a.Main()
