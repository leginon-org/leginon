from appionlib import torqueHost
from appionlib import apRefineJobFrealign
from appionlib import apRefineJobEman
from appionlib import apRefineJobXmipp
from appionlib import apRefineJobRelion
from appionlib import apRefineJobXmippML3D
from appionlib import apRemoteJob
from appionlib import apSparxISAC
from appionlib import apGenericJob
from appionlib import jobtest
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import basicAgent
from appionlib import apParam
import sys
import re
import time
import os

try:
	import MySQLdb
	import sinedon
except ImportError, e:
	sys.stderr.write("Warning: %s, status updates will be disabled\n" % (e))
	statusUpdatesEnabled = False
else:
	statusUpdatesEnabled = True

class Agent (basicAgent.BasicAgent):
	def __init__(self, configFile=None):
		super(Agent,self).__init__(configFile)
		
		self.currentJob = None
		self.statusCkInterval = 30
	
	def Main(self,command):
				
		self.processingHost = self.createProcessingHost()
		
		jobType = self.getJobType(command)
		
		#Not sure if we want pedanticaly issue warning messages 
		#if not jobType:
		#	sys.stderr.write("Warning: Could not determine job type\n")
				 
		try:   
			self.currentJob = self.createJobInst(jobType, command)
		except Exception, e:
			sys.stderr.write("Error: Could not create job inst %s : %s\n" %(command, e))
			sys.exit(1)
			
		if not self.currentJob:
			sys.stderr.write("Error: Could not create job for: %s\n" % (command))
			sys.exit(1)
			
		# Write out the command for this job to the jobs run directory
		self.saveCommandToFile( command )

		if self.currentJob.getSetupOnly():
			sys.stderr.write("Create job but not execute %s\n" % (command))
			sys.exit(1)

		if not self.currentJob.getLaunchAsShell():
			# typical case that put all commands in one queued job script
			hostJobId = self.processingHost.launchJob(self.currentJob)
		else:
			# need to run most commands from head node shell when multiple queued submission is needed in parallel
			hostJobId = self.executeCommandList(self.currentJob)
		#if the job launched successfully print out the ID returned.
		if not hostJobId:
			sys.stderr.write("Error: Could not execute job %s\n" % (self.currentJob.getName()))
			sys.exit(1)
			
		sys.stdout.write(str(hostJobId) + '\n') 
		sys.stdout.flush()
	   
		if statusUpdatesEnabled:
			self.updateJobStatus(self.currentJob, hostJobId)
	   
		return 0
 
	##getJobType (command)
	#Searches a list of command options , 'command',  and attempts to extract the 
	#job type from it.  Returns the job type if successful otherwise returns None.
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

	##	   
	#
	def createJobInst(self, jobType, command):
		jobInstance = None
		print "Job type: %s"%(jobType)	
		if "emanrecon" == jobType:
			jobInstance = apRefineJobEman.EmanRefineJob(command)
		elif "frealignrecon" == jobType:
			jobInstance = apRefineJobFrealign.FrealignRefineJob(command)
		elif "xmipprecon" == jobType:
			jobInstance = apRefineJobXmipp.XmippSingleModelRefineJob(command)
		elif "relionrecon" == jobType:
			jobInstance = apRefineJobRelion.RelionSingleModelRefineJob(command)
		elif "xmippml3d" == jobType:
			jobInstance = apRefineJobXmippML3D.XmippML3DRefineJob(command)
		elif "sparxisac" == jobType:
			jobInstance = apSparxISAC.ISACJob(command)
		elif "jobtest" == jobType:
			jobInstance = jobtest.jobtestClass()
		else:
			jobInstance = apGenericJob.genericJob(command)
		print jobType, command
		return jobInstance

	# This is used to execute commands on the head node, rather than through the resource manager with a job file.
	def executeCommandList(self,jobObject):
		returncode = self.processingHost.executeCommand('rm -f agent.log')
		returncode = self.processingHost.executeCommand('source %s >agent.log &' % (jobObject.commandfile),wait=False)
		return 1

	##
	#
	def updateJobStatus (self, jobObject, hostJobId ):
		checkStatusInterval =  self.statusCkInterval
		currentStatus = 'Q'
						
		projDB = self.__initDB(jobObject, hostJobId)				
		jobid = jobObject.getJobId()
		
		if projDB:
			#Update before forking, indicating to insert new row if necessary.
			self.__updateStatusInDB(jobid, currentStatus)
			
			try:
				pid = os.fork()		
				if pid == 0:
					os.setsid()
					while currentStatus != "D" and currentStatus != "U":
						time.sleep(checkStatusInterval)
						newStatus = self.processingHost.checkJobStatus(hostJobId)
						if newStatus != currentStatus:
							#Assume status changed was missed if we go from R or Q to U (unknown) and mark
							#job as done.
							if newStatus == "U" and (currentStatus == "R" or currentStatus == "Q"):
								currentStatus = "D"
							else:		
								currentStatus = newStatus
							
							self.__updateStatusInDB(jobid, currentStatus)
				   
			except OSError, e:
				sys.stderr.write("Warning: Unable to monitor status: %s\n" % (e))
		else:
			sys.stderr.write("Warning: Unable to monitor job status.\n")					   

		return
	
	# write out a text file with "command" as the only contents to the jobs run dir.
	# The command is a list
	def saveCommandToFile(self, command):
		# create the rundir if it is not there
		rundir = self.currentJob.getRundir()
		apParam.createDirectory( rundir, warning=False )
		
		# set the file path and name and get current  date time to record with the command
		commandLog = os.path.join( rundir, "run_commands.log" )
		datetime = time.strftime("%c")
		
		# We append to this file as many commands can use this run dir and we want to see all of them without overwriting.
		f = open( commandLog, 'a' )
		f.write( datetime )
		f.write( '\nIMPORTANT: To re-run this job, if runJob.py is followed with a path ending in /appion, \nyou must copy this path so that it also occurs at the start of the command, prior to runJob.py. \n\n' )
		f.write( 'runJob.py ' )
		
		for entry in command:
		  f.write( entry + " " )
		  
		f.write( "\n______________________________________________\n")
		f.close()

	##
	#
	def __updateStatusInDB (self, jobid, status):
		retVal = True   #initialize return value to True
		dbConfig = sinedon.getConfig('appiondata')
		dbConnection = MySQLdb.connect(**dbConfig)
		dbConnection.autocommit(True)
		cursor = dbConnection.cursor()
		   
		   
		updateCommand = "UPDATE ApAppionJobData SET status= '%s' WHERE `DEF_id` = '%s'" % (status, jobid)
		result = cursor.execute(updateCommand)
		
		if not result:
			retVal = False
			  
		return retVal

	##
	#
	def __initDB (self, jobObject, job):
		retValue = None
			
		try:
			#Determine the appion project database name using the project id.
			projDBConfig = sinedon.getConfig('projectdata')
			dbConnection = MySQLdb.connect(**projDBConfig)
			dbConnection.autocommit(True)
			cursor =  dbConnection.cursor()
										  
			query = "SELECT appiondb from processingdb WHERE `REF|projects|project`=%d" % (jobObject.getProjectId())
			queryResult=cursor.execute(query)
			if queryResult:
				projDB = cursor.fetchone()[0]
				projDBConfig = sinedon.setConfig('appiondata', db=projDB)
				retValue = projDB
				
			cursor.close()
			dbConnection.close()
		except MySQLdb.DatabaseError, e:
			sys.stderr.write("Warning: Failure determining project database: %s \n" % (e))
		
		#if jobId is not set, assume there is no entry in ApAppionJobData for this run
		if not jobObject.getJobId():
			
			### insert a cluster job
			# TODO: what happens when this runs remotely???		
			
			rundir = jobObject.getRundir()
			pathq = appiondata.ApPathData(path=os.path.abspath(rundir))
			clustq = appiondata.ApAppionJobData()
			clustq['path'] = pathq
			clustq['jobtype'] = jobObject.getJobType()
			clustq['name'] = jobObject.getJobName()
			remoterundir = jobObject.getOutputDir()
			remoterundirq = appiondata.ApPathData(path=os.path.abspath(remoterundir))
			clustq['clusterpath'] = remoterundirq
			clustq['session'] = apDatabase.getSessionDataFromSessionId(jobObject.getExpId())
			clustq['user'] = os.getlogin()
			clustq['cluster'] = os.uname()[1]
			clustq['clusterjobid'] = job
			clustq['status'] = "Q"
			clustq.insert()   
			
		return retValue
			
