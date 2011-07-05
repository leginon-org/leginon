import processingHost

class TorqueHost(processingHost.ProcessingHost):
    def __init__ (self):
        processingHost.ProcessingHost.__init__(self)  #initialize parent
        self.type="Torque"
        self.execCommand="qsub"
        self.statusCommand="qstat"
        self.scriptPrefix="#PBS"
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
            header += self.scriptPrefix +"  -l walltime=" + currentJob.getWalltime()+"\n"
        
        if currentJob.getNodes():
            header += self.scriptPrefix +"  -l nodes=" + currentJob.getNodes()
            if currentJob.getPPN():
                header += ":ppn=" + currentJob.getPPN()
            header += "\n"
        
        if currentJob.getCpuTime():
            header += self.scriptPrefix +"  -l cput=" + currentJob.getCpuTime() + "\n"
            
        if currentJob.getMem():
            header += self.scriptPrefix +"  -l mem=" + currentJob.getMem() + "\n"
        
        if currentJob.getPmem():
            header += self.scriptPrefix +"  -l pmem=" + currentJob.getMem() + "\n"
            
        if currentJob.getQueue():
            header += self.scriptPrefix +" -q " + currentJob.getQueue() + "\n"
            
        if currentJob.getAccount():
            header += self.scriptPrefix +" -A " + currentJob.getAccount()+ "\n"
            
        #Add any custom headers for this processing host.
        for line in self.additionalHeaders:
            header += self.scriptPrefix + line + "\n"            
        #add some white space     
        if self.preExecLines:    
            header += "\n\n"
        #Add any coustom line that should be added to jobfile (Ex. module purge)
        for line in self.preExecLines:
            header += line + "\n"
        #add some white space  
        header += "\n\n"
        return header
    
#translateOutput (outputString)
#Takes the outputSring returned by executing a command (executeCommand()) and
#Translates it into a Job ID which can be used to check job status.  This is 
#fairly simple for Torque since the output of qsub should be a job id of the form
# <id#.servername.domain>
    def traslateOutput (self, outputString):
        outputList = outputString.split('.')
        try:
            jobID= int(outputList[0])
        except:
            return False
        return JobID
        
        
        
        
