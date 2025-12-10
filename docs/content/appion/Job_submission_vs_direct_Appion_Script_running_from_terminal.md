We have two schools of developers.

1.  Some has only single node computer and wants to run appionScript without going through resource manager by constructing Appion script and options directly on the terminal. This means that appionScript need to be able to manage the resource without a resource manager. The users would use **Show Commands** in myamiweb
2.  Some wants to move all appion job running through job submission so that resource managers are used in a large cluster of nodes. The users would use **Submit job** in myamiweb.

This wiki is to organize my (Anchi) findings on what modules does what and how options are passed and set and what are logged into database and when in the two different way of running Appion currently.

## Show Command path (**Bold** are not performed in BasicScript)

### "*init*()"

# createDefaultStats

# set self.functionname as basename of

    sys.argv[0]

1.  **set self.appiondir**
2.  setParams
    1.  **setupGlobalParseOptions** (I have not found any appion script not doing this step even though it can be turned off)
    2.  setupParserOptions (subclasses overwrite appionScript base class that adds stackid).
    3.  convertOptions to self.params
3.  set processing database using projectid (don't see how we can have a situation without projectid any more).
4.  check conflicts
    1.  checkConflicts from subclasses of appionScript
    2.  **checkGlobalConflicts**
5.  **set up run directory**
6.  **start pool of threads** (set to 2 now and will time out if not used in 10 seconds)
7.  writeFunctionLog
8.  **uploadScriptData**
    1.  ProgramName
    2.  UserName
    3.  Host
    4.  ProgramRun (need cluster job id)
        1.  query for ApAppionJobData by
            1.  path = self.params['rundir']
            2.  jobtype = self.functionname
        2.  insert if not exist
        3.  **set ApAppionJobData to Run**
    5.  ParamName and ParamValues

### start()

### close()

1.  closeFunctionLog
2.  **set ApAppionJobData to Done**
