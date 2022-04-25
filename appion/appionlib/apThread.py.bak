#!/usr/bin/env python

## python
import sys
import time
import threading
import Queue
import subprocess
import os
## appion
from appionlib import apDisplay
from appionlib import apParam

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



class LauncherThread(threading.Thread):
	def __init__(self, queue, logfilename):
		threading.Thread.__init__(self)
		self.queue = queue
		#self.setDaemon(True)
		self.logfilename = logfilename

	def log(self, message):
		logfile = open(self.logfilename, 'a')
		logfile.write('%s:  %s\n' % (time.asctime(), message))
		logfile.flush()
		logfile.close()

	def run(self):
		self.log('run start1')
		while True:
			try:
				proc_info = self.queue.get(block=True, timeout=10)
			except Queue.Empty:
				break
			self.log('got from queue')
			self.log(str(proc_info))
			args = proc_info['args']
			kwargs = proc_info['kwargs']
			self.log('starting subprocess')
			self.proc = subprocess.Popen(*args, **kwargs)
			self.proc.wait()
			self.log('subprocess done')
		self.log('thread done')

class ProcessLauncher(object):
	def __init__(self, nproc=1, rundir=None):
		self.queue = Queue.Queue()
		self.nproc = nproc
		if rundir is None:
			self.rundir = os.getcwd()
		else:
			self.rundir = rundir
		self.threads = []
		for i in range(self.nproc):
			logfilename = 'thread%03d.log' % (i,)
			logfilenamepath = os.path.join(self.rundir, logfilename)
			newthread = LauncherThread(self.queue, logfilenamepath)
			self.threads.append(newthread)
			newthread.start()

	def launch(self, *args, **kwargs):
		proc_info = {'args': args, 'kwargs': kwargs}
		self.queue.put(proc_info)

def testProcessLauncher():
	p = ProcessLauncher(4)
	for i in range(8):
		p.launch(['sleep','10'])
		time.sleep(1)


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
		writeThreadLog(cmd)
		job = AppionJob(cmd)
		joblist.append(job)
		job.run()

	### continue until no commands are left
	sys.stderr.write("threading commands")
	while len(localcmdlist) > 0 or len(joblist) > 0:
		for job in joblist:
			if job.poll() is not None:
				joblist.remove(job)
				if len(localcmdlist) > 0:
					cmd = localcmdlist.pop(0)
					writeThreadLog(cmd)
					job = AppionJob(cmd)
					joblist.append(job)
					job.run()
		sys.stderr.write(".")
		time.sleep(pausetime)
		#print joblist
	sys.stderr.write("\n")

#===========
def writeThreadLog(msg):
	f = open("threading.log", "a")
	f.write("%s\t%s\n"%(time.asctime(), msg))
	f.close()

#===========
def testThreadCommands():
	import random
	cmdlist = []
	for i in range(20):
		cmd = "sleep %d"%(random.random()*10)
		cmdlist.append(cmd)
	print cmdlist
	threadCommands(cmdlist)

if __name__ == "__main__":
	testProcessLauncher()



