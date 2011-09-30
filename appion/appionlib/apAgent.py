from appionlib import torqueHost
from appionlib import apRefineJobFrealign
from appionlib import apRefineJobEman
from appionlib import apRefineJobXmipp
from appionlib import apRefineJobXmippML3D
from appionlib import apGenericJob
from appionlib import jobtest
import sys
import re
import subprocess
import time
import os

class Agent (object):
    def __init__(self, configFile=None):
        if configFile:
            self.configFile = configFile
        
        self.currentJob = None
        self.processingHost = None
        
    
    def Main(self,command):
        
        self.processingHost = self.createProcessingHost()
        
        jobType = self.getJobType(command)
        if not jobType:
            sys.stderr.write("Error: Could not determine job type\n")
            sys.exit(1)
         
        try:   
            self.currentJob = self.createJobInst(jobType, command)
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
        self.updateJobStatus(self.currentJob, hostJobId)
        return 0
        
    def createProcessingHost(self):
        if not self.configFile:
            raise ValueError ("Could not create processing host object, configuration file not defined") 
        
        configDict = self.parseConfigFile(self.configFile)
        try:
            processingHostType = configDict['ProcessingHostType'].upper()
            if 'TORQUE' == processingHostType or 'PBS' == processingHostType:
                processingHost = torqueHost.TorqueHost(configDict)
            else:
                sys.stderr.write("Unknown processing host type, using default\n")
                processingHost = torqueHost.TorqueHost(configDict)
            
        except (KeyError, AttributeError):
            sys.stderr.write("Couldn't determine processing host type, using default\n")
            processingHost = torqueHost.TorqueHost(configDict)
 
        return processingHost
       
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
            
    
    def createJobInst(self, jobType, command):
        jobInstance = None
            
        if "emanrecon" == jobType:
            jobInstance = apRefineJobEman.EmanRefineJob(command)
        elif "frealignrecon" == jobType:
            jobInstance = apRefineJobFrealign.FrealignRefineJob(command)
        elif "xmipprecon" == jobType:
            jobInstance = apRefineJobXmipp.XmippSingleModelRefineJob(command)
        elif "xmippml3d" == jobType:
            jobInstance = apRefineJobXmippML3D.XmippML3DRefineJob(command)
        elif "jobtest" == jobType:
            jobInstance = jobtest.jobtestClass()
        else:
            jobInstance = apGenericJob.genericJob(command)
        
        return jobInstance
    
    def parseConfigFile (self, configFile):
        confDict ={}
        try:
            cFile= file(configFile, 'r')
        except IOError, e:
            raise IOError ("Couldn't read configuration file " + configFile + ": " + str(e))
        
        #for line in cFile.readlines():          
        line = cFile.readline()
        while line:
            #get rid of an leading and trailing white space
            #line = line.strip()
            #Only process lines of the correct format, quietly ignore all others"
            matchedLine=re.match(r'\s*([A-Za-z]+)\s*=\s*(\S.*)\s*',line)
            if  matchedLine:
                #split the two parts of the line
                (key, value) = matchedLine.groups()
                #value strings can be spread across multiple lines if \n is escaped (\)
                #process these lines.              
                while '\\' == value[-1]:      
                    value = value[:-1]
                    line= cFile.readline()
                    value += line.rstrip('\n')
                #split comma separated values into a list
                if ',' in value:   
                    value = re.split(r'\s*,\s*', value)
                #put the key/value pair in the configuration dictionary    
                confDict[key]=value
            line = cFile.readline()
                
        return confDict
    
    def updateJobStatus (self, jobObject, jobHostId ):
        checkStatusInterval = 30 #check status every 30 seconds
        currentStatus = 'Q'
        projectId = jobObject.getProjectId()
        jobid = jobObject.getJobId()
        
        #Update before forking
        self.__updateStatusInDB(jobid, currentStatus, projectId)
        
        try:
            pid = os.fork()        
            if pid == 0:
                os.setsid()
                while currentStatus != "D" and currentStatus != "U":
                    time.sleep(checkStatusInterval)
                    newStatus = self.processingHost.checkJobStatus(jobHostId)
                    if newStatus != currentStatus:
                        #Assume status changed was missed if we go from R or Q to U (unknown) and mark
                        #job as done.
                        if newStatus == "U" and (currentStatus == "R" or currentStatus == "Q"):
                            currentStatus = "D"
                        else:        
                            currentStatus = newStatus
                        
                        self.__updateStatusInDB(jobid, currentStatus, projectId)
                        
                    
                    
        except OSError, e:
            sys.stderr.write("Warning: Unable to monitor status: %s\n" % (e) )
       
        return
    
    def __updateStatusInDB (self, jobid, status, projectId):
        retVal = True   #initialize return value to True
        #command string to pass to subprocess
        updateCommand = "updateAppionDB.py %d %s %d" % (jobid,status,projectId)
        
        try:
            process = subprocess.Popen(updateCommand, stdout=subprocess.PIPE, 
                                                  stderr=subprocess.PIPE,  shell = True)
            r = process.wait()
            #Command failed if return value greater than zero
            if r > 0:
                retVal = False
        except Exception:
            retVal = False       
        
        return retVal
