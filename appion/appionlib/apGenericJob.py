import os
import re

class genericJob(object):
    def __init__(self, optList=None):
        #set defalulst
        self.runname = "GenericJob"
        self.command_list = []
        self.wallTime = 2 #2 hours
        self.nodes = 1
        self.ppn = 1
        self.cpuTime = 0
        self.mem = 0
        self.jobid = 0
        self.projectId = 0 
        self.rundir =""      
        if optList:
            newOptList=self.setJobAttributes(optList)
            self.createCommandList(newOptList)
            
    def createCommandList(self, optList ):
        jobId = str(self.getJobId())            #store appion job id as a sting
        projectId = str(self.getProjectId())    #store appion project id as a string
        logFileName = os.path.join(self.getOutputDir(), self.getName()+ ".log")
        
        self.command_list.append("updateAppionDB.py " + jobId + " R " + projectId)
        lineToAdd ="webcaller.py \'"
        #Reconstruct the command line to pass to webcaller in the job file.
        for opt in optList:
            lineToAdd += opt + " "
        
        lineToAdd += "\' " + logFileName
        #Add the reconstructed line to the command list
        self.command_list.append(lineToAdd)
        
        self.command_list.append("updateAppionDB.py " + jobId + " D " + projectId)
        self.command_list.append("exit")
    
    def setJobAttributes (self, optList):
        newCommandLine = []
        options = {'runname'   : self.setName, 
                   'jobid'     : self.setJobId,
                   'rundir'    : self.setOutputDir, 
                   'walltime'  : self.setWallTime, 
                   'cput'      : self.setCpuTime, 
                   'nodes'     : self.setNodes,
                   'ppn'       : self.setPPN,
                   'projectid' : self.setProjectId, 
                   'jobtype'   : (lambda s:s)}
        excludeList = ['jobid', 'walltime', 'cput', 'nodes', 'ppn', 'jobtype']
        optionKeys = options.keys()
        for opt in optList:
            matchedLine = re.match(r'--(\S+)=(.*)', opt)
            if matchedLine:
                (key, value) = matchedLine.groups()

                #if value is a string need to reconstruct opt value adding quotes
                if re.search(r'\s', value):
                    opt = '--' + key + '=' + '\"' + value + '\"'
                    
                #Only copy certain options to the new command line.  Those in the  
                #exclude list are not understood by appion commands.
                if not key in excludeList:
                    newCommandLine.append(opt)

                if key in optionKeys:
                    options[key](value)                
            else:
                #Just pass along any options not in the format expected
                newCommandLine.append(opt)                                
        return newCommandLine
    
                    
    def getWalltime(self):
        return self.wallTime
    def setWallTime(self, time):
        self.wallTime = time      
   
    def getName(self):
        return self.runname 
    def setName(self, newname):
        self.runname = newname + ".appionsub"
                          
    def getNodes(self):
        return self.nodes
    def setNodes(self, numNodes):
        self.nodes = numNodes
        
    def getPPN(self):
        return self.ppn
    def setPPN (self, numProcs):
        self.ppn = numProcs
        
    def getCpuTime(self):
        return self.cpuTime
    def setCpuTime(self,time):
        self.cpuTime = time
        
    def getMem(self):
        return  self.mem
    def setMem(self, memSize):
        self.mem = memSize
        
    def getPmem(self):
        return None
    def getQueue(self):
        return None
    def getAccount(self):
        return None
    
    def getOutputDir(self):       
        return self.rundir
    def setOutputDir(self, dirname):
        if dirname.startswith('~'):
            dirname = os.path.expanduser(dirname)           
        self.rundir = os.path.expandvars(dirname)
        
    def getCommandList(self):
        return self.command_list
    
    def getJobId(self):
        return self.jobid
    def setJobId(self, id):
        self.jobid = int(id)
    def getProjectId(self):
        return self.projectId
    def setProjectId(self, id):
        self.projectId = int(id)