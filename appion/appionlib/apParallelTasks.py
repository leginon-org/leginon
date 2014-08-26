from appionlib import torqueHost
from appionlib import apGenericJob
from appionlib import basicAgent
import sys
import re
import time
import os

statusUpdatesEnabled = True
class SimpleJob(object):
	def __init__(self,command,name='test', rundir='./',ppn=1, nodes=1, mem=2):
		self.wallTime = 2 #2 hours
		self.nodes = nodes
		self.ppn = ppn
		self.nproc = self.nodes * self.ppn
		self.cpuTime = 0
		self.mem = mem
		self.command_list = [command]
		self.name = name
		self.rundir = self.setRunDir(rundir)
		self.runname = 'simple'

	def getRunDir(self):
		return self.rundir
	def setRunDir(self,rundir):
		return os.path.abspath(rundir)

	def getOutputDir(self):	   
		return self.rundir
	def setOutputDir(self, dirname):
		if dirname.startswith('~'):
			dirname = os.path.expanduser(dirname)		   
		self.rundir = os.path.expandvars(dirname)
		
	def getName(self):
		return self.name
	def setName(self, newname):
		self.runname = newname + ".aptask"
						  
	def getNodes(self):
		return self.nodes
	def setNodes(self, numNodes):
		self.nodes = numNodes
		
	def getPPN(self):
		return self.ppn
	def setPPN(self, numProcs):
		self.ppn = numProcs
		
	def getNProc(self):
		return self.nproc
	def setNProc(self, totalNumProcs):
		self.nproc = totalNumProcs
		
	def getWalltime(self):
		return self.wallTime
	def setWallTime(self, time):
		self.wallTime = time	  
		
	def getCpuTime(self):
		return self.cpuTime
	def setCpuTime(self,time):
		self.cpuTime = time
		
	def getMem(self):
		return  self.mem
	def setMem(self, memSize):
		self.mem = memSize
		
	def getPmem(self):
		return None
	def getQueue(self):
		return None
	def getAccount(self):
		return None
	
	def getCommandList(self):
		return self.command_list
	
	def getJobName(self):
		return self.runname + ".job"


class Agent (basicAgent.BasicAgent):
	'''
	create and launch queued job without most appion options.
	The job is logged in task_jobid.save so that it can be
	monitored.
	'''
	def __init__(self,configFile=None,rundir='./'):
		super(Agent,self).__init__(configFile)
		self.taskid_file = os.path.join(os.path.abspath(rundir),'task_jobids.save')
		self.rundir = os.path.abspath(rundir)
		self.setJobHeaderInfo()

	def setJobHeaderInfo(self,ppn=1,nodes=1,mem=2):
		self.ppn = ppn
		self.nodes = nodes
		self.mem = mem

	def Main(self,idtext,commands):
		self.initiateTaskIdFile()
		self.processingHost = self.createProcessingHost()
		self.idtext = idtext

		for command in commands:	 
			try:   
				self.currentJob = self.createJobInst(command)
			except Exception, e:
				sys.stderr.write("Error: Could not create job  %s : %s\n" %(command, e))
				sys.exit(1)
			
			if not self.currentJob:
				sys.stderr.write("Error: Could not create job for: %s\n" % (command))
				sys.exit(1)
			  
			hostJobId = self.processingHost.launchJob(self.currentJob)
			#if the job launched successfully print out the ID returned.
			if not hostJobId:
				sys.stderr.write("Error: Could not execute job %s\n" % (self.currentJob.getName()))
				sys.exit(1)
			
			sys.stdout.write(str(hostJobId) + '\n') 
			sys.stdout.flush()
	   
			self.updateTaskIdFile(hostJobId)
	   
		return hostJobId
 
	#
	def createJobInst(self, command):
		jobInstance = None
			
		jobInstance = SimpleJob(command,self.idtext,self.rundir,ppn=self.ppn,nodes=self.nodes,mem=self.mem)
		return jobInstance
	##
	#
	def initiateTaskIdFile(self):
		if not os.path.isfile(self.taskid_file):
			f = open(self.taskid_file,'w')
			f.close()

	def updateTaskIdFile (self, hostJobId ):
		f = open(self.taskid_file,'a')
		f.write('%d\n' % hostJobId)
		f.close()

if __name__ == "__main__":
	configfile = '/home/acheng/.appion.cfg'
	a = Agent(configfile)
	a.Main('test',['ls','ls -l'])
