#!/usr/bin/python -O

import pyami.quietscipy

#builtin
import sys
import os
import re
import time
import math
import random
import cPickle
import glob
import shutil
import subprocess

#appion
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apImage
from appionlib import apParam
from appionlib import apProject
#leginon
from appionlib import appionLoop2
from pyami import mem

class AppionPBS(appionLoop2.AppionLoop):
	#=====================
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		overrides appionScript
		"""
		appionLoop2.AppionLoop.__init__(self)
	
	#=====================
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""
		appionLoop2.AppionLoop.setupGlobalParserOptions(self)
		
		self.parser.add_option("--usequeue", dest='usequeue', action='store_true', default=False, help='Parallelize by submitting individual jobs to PBS style queue')
		self.parser.add_option("--keepscratch", dest='keepscratch', action='store_true', default=False, help='Keep queue scratch directories')
		self.parser.add_option("--queue_scratch", dest='queue_scratch', type='str', default=None, help='Scratch directory if queueing up jobs')
		self.parser.add_option("--queue_name", dest='queue_name', type='str', default='backfill', help='Name of the queue to use')
		self.parser.add_option("--queue_style", dest='queue_style', type='str', default='PBS', help='Style of the queue to use. Only PBS and MOAB supported.')
		self.parser.add_option("--walltime", dest='walltime', type='int', default='4', help='Walltime for the queue in hours.')
		self.parser.add_option("--queue_memory", dest='queue_memory', type='int', default='2', help='Memory required for queued process. In GB')
		self.parser.add_option("--queue_ppn", dest='queue_ppn', type='int', default='1', help='Processors per node. The default will typically work.')
		self.parser.add_option("--njobs", dest='njobs', type='int', default=1, help='Number of jobs to submit to queue')
		self.parser.add_option("--dryrun", dest='dryrun', action='store_true', default=False,  help="Create jobs but don't submit")

	#=====================
	def run(self):
		"""
		processes all images
		"""
		if not self.params['parallel']:
			self.cleanParallelLock()
		### get images from database
		self._getAllImages()
		os.chdir(self.params['rundir'])
		self.preLoopFunctions()
		### start the loop
		self.notdone=True
		self.badprocess = False
		self.stats['startloop'] = time.time()
		
		while self.notdone:
			apDisplay.printColor("\nBeginning Main Loop", "green")
			imgnum = 0
			while imgnum < len(self.imgtree) and self.notdone is True:
				jobn=1
				print 1
				
				if self.params['usequeue'] is True:
					jobs=[]
					while jobn <= self.params['njobs'] and imgnum < len(self.imgtree):
						#process image(s)
						#finish up stuff
						print 2
						self.stats['startimage'] = time.time()
						imgdata = self.imgtree[imgnum]
						imgnum += 1
						
						#preliminary stuff
						self._preliminary(imgdata)
						
						#process image(s)
						scratchdir=self._setupScratchDir(imgdata)
						targetdict=self.copyTargets(imgdata,scratchdir)
						apDisplay.printMsg('Copying %s data to %s' % (imgdata['filename'], scratchdir))
						
						command=self.generateCommand(imgdata,targetdict)						
						jobname=self.setupJob(scratchdir, imgdata, command)
						
						jobs.append({'jobname':jobname, 'scratchdir': scratchdir,'imgdata':imgdata,'targetdict':targetdict})
						self.launchPBSJob(scratchdir, jobname)
						
						print command
						if self.params['dryrun'] is True:
							print "setting up only the first job and exiting"
							sys.exit()
						jobn+=1
							
					while len(jobs)>0:
						#print len(jobs)
						#print jobs
						#print jobs[0]
						jobdict=jobs[0]
						finished=self.checkJob(jobdict)
						if finished is True:
							apDisplay.printMsg('%s finished' % (jobdict['jobname']))
							results=self.collectResults(jobdict['imgdata'],jobdict['targetdict'])
							self._finish(jobdict['imgdata'],results)
							if self.params['keepscratch'] is False:
								self._cleanupScratchDir(jobdict['scratchdir'])
							
							jobs.pop(0)
						else:
							apDisplay.printMsg('Waiting 1 minute for job %s to complete' % (jobdict['jobname']))
							time.sleep(60) #sleep 1 minute

				else:
					self.stats['startimage'] = time.time()
					imgdata = self.imgtree[imgnum]
					imgnum += 1
					
					#preliminary stuff
					self._preliminary(imgdata)
					
					#process image(s)
					targetdict=getTargets(imgdata)
					command=self.generateCommand(targetdict)
					print command
					if self.params['dryrun'] is True:
						print "just printing the command and exiting"
						sys.exit()
					self.executeCommand(command)
					self.collectResults(imgdata)
				
					#finish up stuff
					self._finish(imgdata)

			if self.notdone is True:
				self.notdone = self._waitForMoreImages()
			#END NOTDONE LOOP
		self.postLoopFunctions()
		self.close()

	def _setupScratchDir (self,imgdata):
		scratchpath=os.path.join(self.params['queue_scratch'],imgdata['filename'])
		if os.path.exists(scratchpath):
			apDisplay.printWarning('scratch directory exists and will be overwritten')
			shutil.rmtree(scratchpath)
		os.mkdir(scratchpath)
		return scratchpath
	
	def _cleanupScratchDir(self,scratchdir):
		apDisplay.printMsg('erasing %s' % (scratchdir))
		shutil.rmtree(scratchdir)
		
	
	def _preliminary(self,imgdata):	
		### set the pixel size
		self.params['apix'] = apDatabase.getPixelSize(imgdata)
		if not self.params['background']:
			apDisplay.printMsg("Pixel size: "+str(self.params['apix']))
	
	def _finish(self,imgdata,results):
		### WRITE db data
		if self.badprocess is False:
			if self.params['commit'] is True:
				if not self.params['background']:
					apDisplay.printColor(" ==== Committing data to database ==== ", "blue")
				self.loopCommitToDatabase(imgdata)
				self.commitResultsToDatabase(imgdata, results)
			else:
				apDisplay.printWarning("not committing results to database, all data will be lost")
				apDisplay.printMsg("to preserve data start script over and add 'commit' flag")
				self.writeResultsToFiles(imgdata, results)
			self.loopCleanUp(imgdata)
		else:
			apDisplay.printWarning("IMAGE FAILED; nothing inserted into database")
			self.badprocess = False
			self.stats['lastpeaks'] = 0

		### FINISH with custom functions

		self._writeDoneDict(imgdata['filename'])
		if self.params['parallel']:
			self.unlockParallel(imgdata.dbid)

# 				loadavg = os.getloadavg()[0]
# 				if loadavg > 2.0:
# 					apDisplay.printMsg("Load average is high "+str(round(loadavg,2)))
# 					loadsquared = loadavg*loadavg
# 					apDisplay.printMsg("Sleeping %.1f seconds"%(loadavg))
# 					time.sleep(loadavg)
# 					apDisplay.printMsg("New load average "+str(round(os.getloadavg()[0],2)))

		self._printSummary()

		if self.params['limit'] is not None and self.stats['count'] > self.params['limit']:
			apDisplay.printWarning("reached image limit of "+str(self.params['limit'])+"; now stopping")
	
	def setupJob(self, scratchdir, imgdata, command):
		jobname=imgdata['filename']+'.sh'
		jobpath=os.path.join(scratchdir,jobname)
		f=open(jobpath,'w')
		f.write('#!/bin/csh\n')
		f.write('#%s -l nodes=1:ppn=%d\n' % (self.params['queue_style']), self.params['queue_ppn'])
		f.write('#%s -l walltime=%d:00:00\n' % (self.params['queue_style'], self.params['walltime']))
		f.write('#%s -l pmem=%dgb\n\n' % (self.params['queue_style'], self.params['queue_memory']))
		f.write('cd %s\n\n' % scratchdir )
		for arg in command:
			f.write('%s ' % arg )
		
		f.close()
		print jobpath
		return(jobname)

	#def setupJob(self, command):
	#	"""
	#	this function sets up a PBS queue job
	#	it must be overwritten by the child class
	#	"""
	#	apDisplay.printError("you did not create a 'setupJob' function in your script")
	#	raise NotImplementedError()

	def launchPBSJob(self,scratchdir, jobname):
		command=[]
		cwd=os.getcwd()
		os.chdir(scratchdir)
		if self.params['queue_style']=='PBS':
			command.append('qsub')
		elif self.params['queue_style']=='MOAB':
			command.append('msub')
		command.append('-q %s' % self.params['queue_name'])
		command.append(jobname)
		print command
		subprocess.call(command)
		os.chdir(cwd)
	
	def checkJob(self,jobdict):
		jobouts=glob.glob(os.path.join(jobdict['scratchdir'],jobdict['jobname']+'*'))
		print jobouts
		if len(jobouts) > 1:
			return True
		else:
			return False

	def getTargets(self,imgdict):
		"""
		this function generates the command that is wrapped by the appion script
		it must be overwritten by the child class
		the child function must return a string that is the command
		"""
		apDisplay.printError("you did not create a 'getTargets' function in your script")
		raise NotImplementedError()
		
	def generateCommand(self,imgdict):
		"""
		this function generates the command that is wrapped by the appion script
		it must be overwritten by the child class
		the child function must return a string that is the command
		"""
		apDisplay.printError("you did not create a 'generateCommand' function in your script")
		raise NotImplementedError()

	def copyTargets(self, imgdict):
		"""
		this function copies the required files to the PBS scratch directory
		it must be overwritten by the child class
		should return imgdict with necessary modifications for the queued job
		"""
		apDisplay.printError("you did not create a 'copyFiles' function in your script")
		raise NotImplementedError()

	def commitResults(self):
		"""
		
		"""
		pass
				
	def collectResults(self, imgdata):
		"""
		this function is for optional post image processing actions
		should be overwritten in child objects
		"""
		apDisplay.printError("you did not create a 'copyFiles' function in your script")
		raise NotImplementedError()
		
				

		

#=====================
class BinLoop(AppionPBS):
	def setupParserOptions(self):
		return
	def checkConflicts(self):
		return
	def collectResults(self, imgdata):
		return		
	def commitToDatabase(self,imgdata):
		print 'this is where you would commit stuff'
		return
		
	def copyTargets(self, imgdict, scratchdir):
		srcpath=os.path.join(imgdict['session']['image path'],imgdict['filename']+'.mrc')
		shutil.copy(srcpath, scratchdir)
		return imgdict
		
	def generateCommand(self, imgdict):
		command=[]
		command.append('proc2d')
		command.append(imgdict['filename']+'.mrc')
		command.append(imgdict['filename']+'.b2.mrc')
		command.append('shrink=2')
		return command

		
	

#=====================
if __name__ == '__main__':
	print "__init__"
	imageiter = BinLoop()
	print "run"
	imageiter.run()

