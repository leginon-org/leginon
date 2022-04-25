#!/usr/bin/env python

#pythonlib
import sys
#appion
from appionlib import apTaskMonitor
from appionlib import apConfig

configfile = apConfig.getAppionConfigFile()
rundir = sys.argv[1]

a = apTaskMonitor.ParallelTaskMonitor(configfile,rundir)
a.Main()
