#!/usr/bin/env python

#pythonlib
import sys
#appion
from appionlib import apParallelTasks
from appionlib import apConfig

configfile = apConfig.getAppionConfigFile()
rundir = sys.argv[1]
indextext = 'tasksender'+sys.argv[2]
ppn = int(sys.argv[3])
nodes = int(sys.argv[4])
mem = int(sys.argv[5])
command = sys.argv[6]

a = apParallelTasks.Agent(configfile,rundir)
a.setJobHeaderInfo(ppn,nodes,mem)
a.Main(indextext,[command])
