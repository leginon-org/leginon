import subprocess
import shutil
import sys
import os
import socket # For hostname

class ProcessingHost (object):
	def __init__ (self):
		self.name=""
		self.appionConfig=None
		self.shell="/bin/sh"
		self.execCommand="qsub"
		self.statusCommand="qstat"
		self.scriptPrefix="#"
		self.currentJob=None
		self.additionalHeaders=[]
		self.preExecLines=[]

	##generateHeaders (jobObject)
	#Takes a job object or no arguments. If jobObject is supplied it uses it to 
	#construct processing host specific resource directives.  If no argument is
	#supplied used the currentJob property set in the class instance. 
	def generateHeaders(self, jobObject=None):
		pass

	##translateOutput (outputString)
	#Takes the outputSring returned by executing a command (executeCommand()) and
	#Translates it into a Job ID which can be used to check job status.	 This is
	#an abstract method that needs to be implemented in the child class.  
	def traslateOutput (self, outputString):
		pass
	
	##checkJobStatus  
	def checkJobStatus(self, procHostJobId):
		pass
			   
	##configure (confDict)
	#
	def configure (self, confDict):
		options = {
				'Shell': self.setShell,
				'ScriptPrefix': self.setScriptPrefix,
				'ExecCommand': self.setExecCommand,
				'AdditionalHeaders':self.addAdditionalHeaders,
				'PreExecuteLines': self.addPreExecutionLines,
				'StatusCommand': self.setStatusCommand
				}
			
		for opt in confDict.keys():
			if opt in options:
				options[opt](confDict[opt])

	##executeCommand (command)	  
	#Takes a the command string, command, and runs it in a subshell.  Returns the
	#contents of whatever was written to standard out.
	#This implementation as written in the base class should work for most job 
	#managers which provide a job submission executable which effectively returns 
	#immediately.  However it may need to be overridden in some child classes where the
	#command may not return right away.	  
	def executeCommand (self, command, wait=True):
		#run the command string in a subshell
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) 
		if wait:
			#Wait for the process to return and set the exit code.
			returnCode = process.wait()
		else:
			return ''
		
		#if the command program did not execute normally raise an exception and 
		#include the contents of stderr in the message.
		if returnCode > 0:
			errOutput = process.communicate()[1]
			raise OSError ("Job execution command exited abnormally. " + errOutput)		  
		
		#return what we get from stdout
		return process.communicate()[0]
								 
	##createJobFile(jobFile, jobObject)
	#Takes a file handle open for writing and optionally a job object from which it will
	#generate the job headers and extract the list of commands.	 The generated job file
	#is written to the supplied file.  
	def createJobFile(self, jobFile, jobObject=None):
		if jobObject:
			currentJob=jobObject
		elif self.currentJob:
			currentJob=self.currentJob
		else:
			raise UnboundLocalError ("Current Job not set")		
		
		#Generate the processing host specific headers for the job file
		host      = socket.gethostname()
		header    = self.generateHeaders(currentJob)
		commandList = currentJob.getCommandList()		
		try:
			jobFile.write(header)		   
			jobFile.write("\n# Target Host: " + host + "\n")
			jobFile.write("# This job file has been created for the %s processing host. \n# Changes may be required to run this on another host.\n\n" % (host))
			for line in commandList:
				jobFile.write(line + '\n')
		except IOError, e:
			sys.stderr.write("Could not write to job file" + jobFile.name + ": " + str(e))
			return False
		#Job file was successfully written 
		return True
	   
	##launchJob (jobObject)
	#Takes a object representing the job to be ran, jobObject, creates the job	 
	#script file and executes the job on the processing host.  Returns a 
	#numerical job ID or False if job execution failed.		 
	def launchJob(self, jobObject):
		self.setCurrentJob(jobObject)  #Set the current job 
				
		outputDir= self.currentJob.getOutputDir()
		#Expand ~ and ~user constructions in the output directory string
		if outputDir.startswith('~'):
			outputDir = os.path.expanduser(outputDir)
		
		#Expand any shell variables in the output directory string
		outputDir = os.path.expandvars(outputDir)
   
		#Make sure output directory exist before trying to write a file there.
		if	not os.path.exists(outputDir):
			try:
				os.makedirs(outputDir, 0775)
			except OSError, e:
				sys.stderr.write("Couldn't create output directory " + outputDir + ": " + str(e))
				return False
		
		#Set the absolute path name to the jobfile
		jobfileName = os.path.join(outputDir, self.currentJob.getName() + ".job")
	
		try:
			#open the job file for writing
			jobFile = open(jobfileName, 'w')
		except IOError, e:
			sys.stderr.write("Could not open file to create job file: " + str(e) + "\n")
			return False
		
		self.createJobFile(jobFile)

		jobFile.close()
		#Construct the command string to execute the job.		   
		commandString = "cd " + outputDir + ";"	 
		commandString = commandString + self.execCommand + " " + jobfileName
		try:
			returnValue=self.executeCommand(commandString)
		except (OSError, ValueError), e:
			sys.stderr.write("Failed to execute job " + jobObject.getName() + ": " + str(e))
			return False
	
		#translate whatever is returned by executeCommand() to a JobID	   
		jobID = self.translateOutput(returnValue)
		#return the translated output 
		return jobID
	
	#Beginning of access methods definitions.
	def getShell(self):
		return self.shell
		
	def setShell(self, shell):
		if not isinstance(shell, str):
			raise TypeError ("Argument type should be a string") 
		else:
			self.shell = shell
		
	def getExecCommand(self):
		return self.execCommand
		
	def setExecCommand(self, execCmd):
		if not isinstance(execCmd, str):
			raise TypeError ("Argument type should be a string") 
		else:
			self.execCommand = execCmd
	
	def setStatusCommand (self, statusCmd):
		if not isinstance(statusCmd, str):
			raise TypeError ("Argument type should be a string") 
		else:
			self.statusCommand = statusCmd
		
	def getStatusCommand (self): 
		return	self.statusCommand
				
	def getScriptPrefix(self):
		return self.scriptPrefix
		
	def setScriptPrefix(self, prefix):
		if not isinstance(prefix, str):
			raise TypeError ("Argument type should be a string") 
		else:
			self.scriptPrefix = prefix
			 
	def getCurrentJob(self):
		return self.currentJob
		
	def setCurrentJob(self, jobObject):
		self.currentJob = jobObject
			
	def getAdditionalHeaders(self):
		return self.additionalHeaders
		
	## Used to add addition processing host specific directive headers to
	#every job file that is created.  (Ex. ['-j oe', '-m oe'])
	def addAdditionalHeaders(self, headers):
		if not isinstance(headers, list):
			raise TypeError ("Argument type should be a list")
		else:
			self.additionalHeaders += headers
		
	def getPreExecutionLines(self):
		return self.preExecLines
		
	##Used to added addition command lines to every job script.	 The lines
	#will be executed before the rest of the commands in the script.  
	def addPreExecutionLines(self, lineList):
		if not isinstance(lineList, list):
			raise TypeError ("Argument type should be a list")
		else:
			self.preExecLines += lineList
				
	   
