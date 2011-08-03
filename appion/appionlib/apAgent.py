import torqueHost
import apRefineJobFrealign
import apRefineJobEman
import apRefineJobXmipp
import apGenericJob
import sys
import re
import subprocess
import time
import os
import jobtest

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
            sys.stderr.write("Error: Could not create job "  +  str(command) + ": " + str(e) + '\n')
            sys.exit(1)
        
        if not self.currentJob:
              sys.stderr.write("Error: Could not create job for: " + str(command))
              sys.exit(1)
              
        hostJobId = self.processingHost.launchJob(self.currentJob)
        #if the job launched successfuly print out the ID returned.
        if not hostJobId:
            sys.stderr.write("Error: Could not execute job " + self.currentJob.getName()+ "\n")
            sys.exit(1)
            
        sys.stdout.write(str(hostJobId) + '\n') 
        sys.stdout.flush()
        self.updateJobStatus(self.currentJob, hostJobId)
        return 0
        
    def createProcessingHost(self):
        if not self.configFile:
            raise ValueError ("Could not create processing host object, configureaton file not defined") 
        
        configDict = self.parseConfigFile(self.configFile)
        try:
            processingHostType = configDict['ProcessingHostType'].upper()
            if 'TORQUE' == processingHostType or 'PBS' == processingHostType:
                processingHost = torqueHost.TorqueHost(configDict)
            else:
                sys.stderr.write("Unkown processing host type, using defalut\n")
                processingHost = torqueHost.TorqueHost(configDict)
            
        except (KeyError, AttributeError):
            sys.stderr.write("Couldn't determine processing host type, using default\n")
            processingHost = torqueHost.TorqueHost(configDict)
 
        return processingHost
       
    ##getJobType (command)
    #Searches a list of command optons , 'command',  and attempts to extraqct the 
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
            jobInstatnce = apRefineJobFrealign.FrealignRefineJob(command)
        elif "xmipprecon" == jobType:
            jobInstance = apRefineXmipp.XmippSingleModelRefineJob(command)
        elif "xmippml3drecon" == jobType:
            jobInstance = apRefineXmippml3d.XmippMl3dRefineJob(command)
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
            #get rid of an leadig and trailing white space
            #line = line.strip()
            #Only process lines of the correct format, quitly ignore all others"
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
                #split comma seperated values into a list
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
                        currentStatus = newStatus
                        self.__updateStatusInDB(jobid, currentStatus, projectId)
                        
                    
                    
        except OSError, e:
            sys.stderr.write("Warning: Unable to monitor status: " + str(e) )
       
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
