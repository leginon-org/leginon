import sys
import time
import subprocess

class RefineOnCluster(object):
	def __init__(self):
		self.ppn = 8
		self.numiter = 1
		self.mem = 2
		self.qsub = 'qsub'
		self.refine_launcher = 'none'
		#self.notifyAppionJobRun()
		#self.syncPrepedFilesWithLocalDisk()
		#self.validateJobMem(self.ppn)

	def finish(self):
		'''
		do what is needed to finish
		'''
		#self.syncResultFilesWithLocalDisk()
		#self.notifyAppionJobDone()
		return

	def syncPrepedFilesWithLocalDisk(self):
		'''
		copy the stack and model files if needed (cluster dependent)
		'''
		sync_scripts = []
		self.jobtasks.expand(sync_scripts)

	def validateJobMem(self,ppn):
		# make sure the cluster node memory can handle the memory requirement
		'''
		These are what I found from the current appion refinement scripts
		'''
		if self.refinetype == 'EMAN':
			min_ang_increment = min(self.angs)
			maxmem = max(self.calcRefineMemEMAN(ppn,self.boxsize,self.symm,min_ang_increment,ppn))
		if self.refinetype == 'Xmipp':
			maxmem = 2
		if self.refinetype == 'Frealign':
			maxmem = self.calcRefineMemFrealign(ppn,self.boxsize)
		if maxmem > self.node_mem:
			sys.exit("Not Enough Memory assigned to do all refinements in the Job")
		# if memory is given by the user, use that
		self.mem = max(self.mem,maxmem)

	def makeRefineScript(self,iter):
			'''
			Need to be implemented in the subclass
			'''
			return [[]]

	def makeMPIMasterScript(self,nprocs,cmds):
		'''
			if there is only one script, append mpi header only
			if there is more than one script, make a master script
			
			Just a mock-up now
		'''
		if len(cmds) > 1:
			mpiapp = ', '.join(cmds)
			return "mpirun --hostfile $PBS_NODEFILE -np %d --app %s\n" % (max(nprocs),mpiapp)
		else:
			return "mpirun --hostfile $PBS_NODEFILE -np %d %s\n" % (nprocs[0],cmds[0])

	def setupRun(self):
		self.jobtasks = []
		for iter in range(self.numiter):
			tasks = self.makeRefineScript(iter)
			'''
			Tasks for the iteration is a list of list
			'''
			if self.refine_launcher == 'none':
				'''
				straight forward script appending to the main job
				'''
				for task in tasks['scripts']:
					for proc in task:
						self.jobtasks.append(proc)
			elif self.refine_launcher == 'mpi':
				'''
				use mpi to parallel processing
				'''
				for itask in range(len(tasks['files'])):
					mpi_sh_script = self.makeMPIMasterScript(tasks['nproc'][itask],tasks['files'][itask])
					self.jobtasks.append(mpi_sh_script)
			elif self.refine_launcher == 'qsub':
				'''
				use qsub equivalent to parallel processing
				'''
				for itask in range(len(tasks['scripts'])):
					parallelprocscripts = []
					for iproc, script in enumerate(tasks['scripts'][itask]):
						'''
						wait for multiple qsub to fake oversubscribed mpi
						'''
						procheader = self.makeJobHeader(tasks['mem'][itask][iproc])
						procscript = procheader + script
						procjobfile = tasks['files'][itask][iproc]+'.job'
						qsub_script = self.writeScript(procscript,procjobfile)
						parallelprocscripts.append(qsub_script)
					self.jobtasks.append(parallelprocscripts)
			#self.appendGetResolutionTask(iter)
			#self.appendAppionResultNamingTask(iter)

	def runSingleThreadCommand(self,cmd):
		'''
		This is a fake runSingleThreadCommand for testing
		'''
		print cmd
		return None

	def RealrunSingleThreadCommand(self,cmd):
		'''
		This is the real runSingleThreadCommand
		'''
		proc=subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		proc.wait()
		return self.getJobId(proc)

	def parseJobId(self,proc):
		'''
		Cluster dependent jobId parsing
		The result should be a unique name and
		a part of the queue running status command result
		if the job is still running
		'''
		return proc.stdout.readlines()[0].strip().split('.')[0]

	def getJobId(self,proc):
		if self.refine_launcher in ('none','mpi'):
			return None
		elif self.refine_launcher in ('qsub'):
			return self.parseJobId

	def waitForParallelTaskDone(self,jobids):
		'''
		This is a fake example
		'''
		for jobid in jobids:
			print 'pretend to wait for %s' % str(jobid)
			time.sleep(2)

	def RealwaitForParallelTaskDone(self,jobids):
		running=True
		while running:
			cmd=[self.qstat]
			print cmd
			proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			proc.wait()
			lines=proc.stdout.readlines()
		
			running=False
			for line in lines:
				words=line.split()
				if len(words) > 0 and (words[0] in jobids):
					print words[0], jobids			
					running=True
					print "waiting 5 minutes for jobs to finish"
					time.sleep(300)
					break

	def makeJobHeader(self,mem):
		header = 'header mem= %.1fgb\n' % float(mem)
		return header

	def writeScript(self,script,filepath):
		'''
		Write to the file the script text and return the qsub command
		'''
		file = open(filepath,'w')
		file.write(script)
		file.close()
		return '%s %s' % (self.qsub,filepath)

	def run(self):
		if self.refine_launcher in ('none','mpi'):
			jobheader = self.makeJobHeader(self.mem)
			jobscript = jobheader
			for taskscript in self.jobtasks:
				jobscript += taskscript
			subprocs = [(self.writeScript(jobscript,'master.job'))]
			self.runSingleThreadCommand(subprocs)
		elif self.refine_launcher in ('qsub'):
			for parallel_tasks in self.jobtasks:
				alljobids = []
				for task in parallel_tasks:
					jobid = self.runSingleThreadCommand(task)
					alljobids.append(jobid)
				self.waitForParallelTaskDone(alljobids)

class Tester(RefineOnCluster):
	def makeRefineScript(self,iter):
			tasks = {
					'mem':[[2,2,2,2],[47,]],
					'scripts':[['echo "doing proc000"\n',
								'echo "doing proc001"\n',
								'echo "doing proc002"\n',
								'echo "doing proc003"\n',
								],
								['frealign.exe combine\n'],],
					'files':[['iter1.proc000.sh',
								'iter1.proc001.sh',
								'iter1.proc002.sh',
								'iter1.proc003.sh',
								],
								['iter1.combine.sh',]],
					'nproc':[[1,1,1,1],[self.ppn]],
					}
			return tasks

if __name__ == '__main__':
	app = Tester()
	app.setupRun()
	app.run()
	app.finish()
	sys.exit()
