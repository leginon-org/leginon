import subprocess
import sys
from appionlib import processingHost

class TorqueHost(processingHost.ProcessingHost):
	def __init__ (self, configDict=None):
		processingHost.ProcessingHost.__init__(self)  #initialize parent
		self.type="Torque"
		self.execCommand="qsub"
		self.statusCommand="qstat"
		self.scriptPrefix="#PBS"
		if configDict:
			self.configure(configDict)

	##generateHeaders (jobObject)
	#Takes a job object or no arguments. If jobObject is supplied it uses it to 
	#construct processing host specific resource directives.  If no argument is
	#supplied used the currentJob property set in the class instance.		 
	def generateHeaders(self, jobObject=None):
		if jobObject != None:
			currentJob=jobObject
		elif self.currentJob != None:
			currentJob=self.currentJob
		else:
			raise UnboundLocalError ("Current Job not set")
		#Every Shell Script starts by indicating shell type
		header = "#!" + self.getShell() + "\n"
			   
		#add job attribute headers
		if currentJob.getWalltime():
			header += self.scriptPrefix +" -l walltime=" + str(currentJob.getWalltime())+":00:00\n"
		
		if currentJob.getNodes():
			header += self.scriptPrefix +" -l nodes=" + str(currentJob.getNodes())
			if currentJob.getPPN():
				header += ":ppn=" + str(currentJob.getPPN())
			header += "\n"
		
		if currentJob.getCpuTime():
			header += self.scriptPrefix +" -l cput=" + str(currentJob.getCpuTime()) + ":00:00\n"
			
		if currentJob.getMem():
			header += self.scriptPrefix +" -l mem=" + str(currentJob.getMem()) + 'gb\n'
		
		if currentJob.getPmem():
			header += self.scriptPrefix +" -l pmem=" + str(currentJob.getPmem()) + "mb\n"
			
		if currentJob.getQueue():
			header += self.scriptPrefix +" -q " + currentJob.getQueue() + "\n"
			
		if currentJob.getAccount():
			header += self.scriptPrefix +" -A " + currentJob.getAccount()+ "\n"
			
		#Add any custom headers for this processing host.
		for line in self.getAdditionalHeaders():
			header += self.scriptPrefix + " " + line + "\n"			   
		#add some white space	  
		if self.preExecLines:	 
			header += "\n\n"
		#Add any custom line that should be added to jobfile (Ex. module purge)
		for line in self.getPreExecutionLines():
			header += line + "\n"
		#add some white space  
		header += "\n\n"
		return header
	
	#translateOutput (outputString)
	#Takes the outputSring returned by executing a command (executeCommand()) and
	#Translates it into a Job ID which can be used to check job status.	 This is 
	#fairly simple for Torque since the output of qsub should be a job id of the form
	# <id#.servername.domain>
	def translateOutput (self, outputString):
		outputList = outputString.split('.')
		try:
			jobID= int(outputList[0])
		except Exception:
			return False
		return jobID	  
		
	
	def checkJobStatus(self, procHostJobId):
		statusCommand = self.getStatusCommand() + " " +	 str(procHostJobId)
		
		try:
			process = subprocess.Popen(statusCommand, 
										stdout=subprocess.PIPE, 
										stderr=subprocess.PIPE, 
										shell=True)
			returnCode =process.wait()
			
			if returnCode != 0:
				#return unknown status if check resulted in a error
				returnStatus = 'U'
			else:
				rstring = process.communicate()[0]
				status =  rstring.split('\n')[2].split()[4]
				#translate torque status codes to appion codes
				if status == 'C' or status == 'E':
					#Job completed of is exiting
					returnStatus = 'D'
				  
				elif status == 'R':
					#Job is running
					returnStatus = 'R'
				else:
					#Interpret everything else as queued
					returnStatus = 'Q'
				
		except Exception:
			returnStatus = 'U'

		return returnStatus
	
class MoabTorqueHost(TorqueHost):
	def __init__ (self, configDict=None):
		super(MoabTorqueHost,self).__init__(configDict)
		if self.type !="MoabTorque":
			sys.stderr.write("Bad processing Host configuration")
			sys.exit(1)

	def translateOutput (self, outputString):
		try:
			jobID= int(outputString.splitlines()[1])
		except Exception:
			return False
		return jobID      
