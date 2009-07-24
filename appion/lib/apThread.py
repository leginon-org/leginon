#!/usr/bin/env python

## python
import sys
import time
import threading
import subprocess
## appion
import apDisplay
import apParam

#===========
class AppionJob(threading.Thread):
	proc = None
	def __init__ (self, cmd):
		threading.Thread.__init__(self)
		self.command = cmd
	def run(self):
		devnull = open('/dev/null', 'w')
		#print self.command
		self.proc = subprocess.Popen(self.command, shell=True, stdout=devnull, stderr=devnull)
		#self.proc.wait()
	def poll(self):
		return self.proc.poll()

#===========
def threadCommands(commandlist, nproc=None, pausetime=1.0):
	"""
	takes a list of commands and runs N of them at a time
	waits for one to finish and submits another thread
	caveats:
		only work on a single machine
	"""
	### set number of processes at a time
	if nproc is None:
		nproc = apParam.getNumProcessors()
	if len(commandlist) < nproc:
		nproc = len(commandlist)

	### copy the list so we don't modify the original
	localcmdlist = commandlist
	joblist = []

	### initialize threads
	for i in range(nproc):
		cmd = localcmdlist.pop(0)
		job = AppionJob(cmd)
		joblist.append(job)
		job.run()

	### continue until no commands are left
	sys.stderr.write("threading commands")
	while len(localcmdlist) > 0 and len(joblist) > 0:
		for job in joblist:
			if job.poll() is not None:
				joblist.remove(job)
				if len(localcmdlist) > 0:
					cmd = localcmdlist.pop(0)
					job = AppionJob(cmd)
					joblist.append(job)
					job.run()	
		sys.stderr.write(".")
		time.sleep(pausetime)
		#print joblist
	sys.stderr.write("\n")

#===========
if __name__ == "__main__":
	import random
	cmdlist = []
	for i in range(20):
		cmd = "sleep %d"%(random.random()*10)
		cmdlist.append(cmd)
	print cmdlist
	threadCommands(cmdlist)





