import processingHost
import torqueHost
import apRefineJobFrealign
import apRefineJobEman
import sys
import re
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
            sys.stderr.write("Error: Could not create job " + self.currentJob.getName() + ": " + str(e) + '\n')
            sys.exit(1)
            
        hostJobId = self.processingHost.launchJob(self.currentJob)
        #if the job launched successfuly print out the ID returned.
        if not hostJobId:
            sys.stderr.write("Error: Could not execute job " + self.currentJob.getName()+ "\n")
            sys.exit(1)
            
        sys.stdout.write(hostJobId)         
        self.updateJobStatus(self.currentJob, hostJobID)
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
            jobInstatnce = apRefineJobEman.EmanRefineJob(command)
        elif "frealignrecon" == jobType:
            jobInstatnce = apRefineJobFrealignJob(command)
        elif "xmipprecon" == jobType:
            jobInstance = apRefineXmipp.XmippRefineJob(command)
        elif "xmippml3drecon" == jobType:
            jobInstance = apRefineXmippml3d.XmippMl3dRefineJob(command)
        elif "jobtest" == jobType:
            jobInstance = jobtest.jobtestClass()
        else:
            raise TypeError ("Unkown job type " + jobType)
        
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
                #split the two parts fo the line
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
        pass
                
                

    
