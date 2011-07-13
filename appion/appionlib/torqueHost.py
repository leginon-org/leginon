import processingHost

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
        header = "#!" + self.shell + "\n"
               
        #add job attributre headers
        if currentJob.getName():
            header += self.scriptPrefix +" -N " + currentJob.getName() + "\n"
        
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
            header += self.scriptPrefix +" -l mem=" + str(currentJob.getMem()) + 'mb\n'
        
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
    #Translates it into a Job ID which can be used to check job status.  This is 
    #fairly simple for Torque since the output of qsub should be a job id of the form
    # <id#.servername.domain>
    def translateOutput (self, outputString):
        outputList = outputString.split('.')
        try:
            jobID= int(outputList[0])
        except Exception:
            return False
        return jobID      
        
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
                
        