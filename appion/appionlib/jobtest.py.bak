class jobtestClass (object):
    def __init__ (self):
        self.name="testjob"
        self.wallTime =2
        self.nodes=4
        self.PPN=4
        self.cpuTime=32
        self.memory=32
        self.pMem = 2
        self.queue="batch"
        self.account="12cs"
        self.outputDir="~/workspace/scratch"
        self.commandList = ['cat  $PBS_NODEFILE','echo "+++++++++++++"','/usr/local/bin/mpirun hostname']
               
    def getWalltime (self):
        return self.wallTime
    def getName(self):
        return self.name                   
    def getNodes(self):
        return self.nodes
    def getPPN(self):
        return self.PPN
    def getCpuTime(self):
        return self.cpuTime
    def getMem(self):
        return  self.memory
    def getPmem(self):
        return self.pMem
    def getQueue(self):
        return self.queue
    def getAccount(self):
        return self.account
    def getOutputDir(self):
        return self.outputDir
    def getCommandList(self):
        return self.commandList