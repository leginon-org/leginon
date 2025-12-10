Moving forward, refinements will all be split into 2 steps, prep and run.

## Prepare refine

When the user selects to prep a refinement, a web form is provided to select the:

1.  refinement method - eman, xmipp, frealign, etc...
2.  stack
3.  model
4.  run parameters - runname, rundir, description
5.  stack prep params - lp, hp, last particle, binning

The web server then calls prepRefine.py located on the local cluster to prepare the refinement.

## Run Refine

When the user selects to run a prepared refinement, a web form is provided to select the:

1.  prepped refine
2.  cluster parameters - ppn, nodes, walltime, cputime, memory, mempernode
3.  refine params, both general and method specific

The web server will then:

1.  verify the cluster params by checking default_cluster.php
2.  if needed, copy the stack and model to a location that can be accessed by the selected cluster
3.  verify the user is logged into the cluster
4.  pass the refine command to runJob.py (extended from the Agent class), located on the remote cluster

runJob.py will:

1.  set the job type which was passed in the command
2.  create an instance of the job class based on the job type
3.  create an instance of the processing host class
4.  launch the job via the processing host
5.  update the job status in the appion database (do we have db access from the remote cluster?)

## Object Model

### Processing Host

Each processing host (eg. Garibaldi, Guppy, Trestles) will define a class extended from a base ProcessingHost class.
The extended classes know what headers need to be placed at the top of job files and they know how to execute a command based on the specific clusters requirements.
The base ProcessingHost class could be defined as follows:

    abstract class ProcessingHost():
        def generateHeader(jobObject) # abstract, extended classes should define this, returns a string
        def executeCommand(command) # abstract, extending classes define this
        def createJobFile(header, commandList) # defined in base class, commandList is a 2D array, each row is a line in the job file.
        def launchJob(jobObject) # defined in base class, jobObject is an instance of the job class specific to the jobtype we are running
            header = generateHeader(jobObject)
            jobFile = createJobFile(header, jobObject.getCommandList())
            executeCommand(jobFile)

### Job

Each type of appion job (eg Emanrefine, xmipprefine) will define a class that is extended from a base Job class.
The extending classes know parameters that are specific to the job type and how to format the parameters for the job file.
The base Job class could be defined as follows:

    class Job():
        self.commandList
        self.name
        self.rundir
        self.ppn
        self.nodes
        self.walltime
        self.cputime
        self.memory
        self.mempernode
        def __init__(command) # constructor takes the command (runJob.py --runname --rundir ....)
            self.commandList = self.createCommandList(paramDictionary)   
        def createCommandList(command) # defined by sub classes, returns a commandList which is a 2D array where each row corresponds to a line in a job file

### Agent

There will be an Agent class that is responsible for creating an instance of the appropriate job class and launching the job.
It will be implemented as a base class, where sub classes may override the createJobInst() function. For now, there will be only one sub class defined
called RunJob. The same runJob.py will be installed on all clusters. This implementation will allow flexibility for the future.
The base Agent class may be defined as follows:

    class Agent():
        def main(command):
            jobType = self.getJobType(command)
            job = self.createJobInst(jobType, command)
            processHost = new ProcessingHost()
            jobId = processHost.launchJob(job)
            self.updateJobStatus()
        def getJobType(command) # parses the command to find and return the jobtype
        def createJobInst(jobType, command) # sub classes must override this the create the appropriate job class instance
        def updateJobStatus() # not sure about how this will be defined yet

Sub classes of Agent will define the createJobInst() function.
We could create a single subclass that creates a job class for every possible appion job type.
(we could make a rule that job sub classes are named after the jobtype with the word job appended. then this function would never need to be modified)
A sample implementation is:

    class RunJob(Agent):
        def createJobInst(jobType, command)
            switch (jobType):
                case "emanrefine":
                    job = new EmanJob(command)
                    break
                case "xmipprefine":
                    job = new XmippJob(command)
                    break
             return job
