import subprocess
import shutil
import sys
import os

class ProcessingHost (object):
    def __init__ (self):
        self.name=""
        self.appionConfig=None
        self.shell="/bin/sh"
        self.execCommand="qsub"
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
#Translates it into a Job ID which can be used to check job status.  This is
#an abstract method that needs to be implimented in the child class.  
    def traslateOutput (self, outputString):
        pass
        
##executeCommand (command)    
#Takes a the command string, command, and runs it in a subshell.  Returns the
#contents of whatever was written to standard out.
#This implimentation as written in the base class should work for most job 
#managers which provide a job submission executable which effectively returns 
#imediately.  However it may need to be overridden in some child classes where the
#command may not return right away.   
    def executeCommand (self, command):
        #run the command string in a subshell
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) 
        #Wait for the process to return a set the exit code.
        returnCode = process.wait()
        
        #if the command program did not execute normaly raise an exception and 
        #include the contents of stderr in the message.
        if returnCode > 0:
            errOutput = process.communicate()[1]
            raise OSError ("Job execution command exited abnormally. Return Code" + returnCode)       
        
        #return what we get from stdout
        return process.communicate()[0]
                                 
##createJobFile(header, commandList)
#Takes a string, header,  which should be a cluster spacific job file header 
#and a list of strings, commandList, which are the individual lines of the job
#file.  Returns a  string which is the absolute path to the temporary job file created.
    def createJobFile(self, header, commandList, jobFile):        
        try:
            jobFile.write(header)          
            for line in commandList:
                jobfile.write(line + '\n')
        except IOError, e:
            sys.stderr.write("Could not write to job file" + jobFile.name + ": " + e)
            return False
        #Job file was successfully writen 
        return True

##launchJob (jobObject)
#Takes a object representing the job to be ran, jobObject, creates the job   
#script file and executes the job on the processing host.  Returns a 
#numerical job ID or False if job execution failed.        
    def launchJob(self, jobObject):
        self.currentJob = jobObject  #Set the current job 
        
        #Generate the processing host specific headers for the job file
        header = self.generateHeader()
        
        outputDir= self.currentJob.getOutputDir()
        #Expand ~ and ~user constructions in the output directory string
        if outputDir.startswith('~'):
            outputDir = os.path.expanduser(outputDir)
        
        #Expand any shell variables in the output directory string
        outputDir = os.path.expandvars(outputDir)
   
        #Make sure output directory exist before trying to write a file there.
        if  not os.path.exists(outputDir):
            try:
                os.makedirs(outputDir, 0775)
            except OSError, e:
                sys.stderr.write("Couldn't create output directory " + outputDir + ": " + e)
                return False
        
        #Set the absolute path name to the jobfile
        jobfileName = OutputDir + "/" + self.currentJob.getName() + ".job"
    
        try:
            #open the job file for writing
            jobFile = file(jobfileName, 'w')
        except IOError, e:
            sys.stderr.write("Could not open file to create job file: " + e)
            return False
        
        self.createJobFile(header, self.currentJob.getCommandList(), jobFile)
        
        #Construct the command string to execute the job.          
        commandString = "cd " + jobObject.getOutputDir() + ";"  
        commandString = commandString + self.execCommand + " " + jobfileName
        try:
            returnValue=self.executeCommand(commandString)
        except (OSError, ValueError), e:
            sys.stderr.write("Failed to execute job " + jobObject.getName() + ": " + e)
            return False
    
        #trasnlate whatever is returned by executeCommand() to a JobID     
        jobID = self.traslatedOutput(returnValue)
        #return the translated output 
        return jobID
    
        #Beginning of accessor methond definitions.
        def getShell(self):
            return self.shell
        
        def setShell(self, newShell):
            self.shell = newShell
        
        def getExecCommand(self):
            return self.execCommand
        
        def setExecCommand(self, execCmd):
            self.execCommand = execCmd
        
                
        def getScriptPrefix(self):
            return self.scriptPrefix
        
        def setScriptPrefix(self, prefix):
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
        
        ##Used to added addition command lines to every job script.  The lines
        #will be executed before the rest of the commands in the script.  
        def addPreExecutionLines(self, lineList):
            if not isinstance(lineList, list):
                raise TypeError ("Argument type should be a list")
            else:
                self.preExecLines += lineList
                
       