#!/usr/bin/env python

import sys
import os
import inspect
from appionlib import apAgent

#=================
def getAppionDir():
    ### convoluted way to get location of this file
    appiondir = None
    this_file = inspect.currentframe().f_code.co_filename
    libdir = os.path.dirname(this_file)  #result: appion/bin
    libdir = os.path.abspath(libdir)     #result: /path/to/appion/bin
    trypath = os.path.dirname(libdir)    #result: /path/to/appion
    if os.path.isdir(trypath):
        appiondir = trypath
    return appiondir

#=================
def getAppionConfigFile():
    homedir = os.path.expanduser('~')    
    configfile = os.path.join(homedir, ".appion.cfg")
    
    if not os.path.isfile(configfile):	
        appiondir = getAppionDir()
        configfile = os.path.join(appiondir, ".appion.cfg")

    if not os.path.isfile(configfile):
        sys.stderr.write("Appion config file : " + configfile 
				+ " doesn't exist.  Can't setup processing host\n")
        sys.exit(1)

    return configfile

#=================
if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.stderr.write("Usage:\n")
        sys.stderr.write(sys.argv[0] + " <options>\n")
        sys.exit(1)

    configfile = getAppionConfigFile()
        
    agent = apAgent.Agent(configfile)
    agent.Main(sys.argv[1:])
    
    sys.exit(0)

  

