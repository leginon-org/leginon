#!/usr/bin/env python

import sys
import os
from appionlib import apAgent

if __name__ == '__main__':

    if len(sys.argv) == 1:
        sys.stderr.write("Usage:\n")
        sys.stderr.write(sys.argv[0] + " <options>\n")
        sys.exit(1)
     
    homedir = os.path.expanduser('~')    
    
    configfile = homedir + "/.appion.cfg"
    
    if not os.path.exists(configfile):
        sys.stderr.write("Appion config : " + configfile + " doesn't exist.  Can't setup processing host\n")
        sys.exit(1)
        
    agent = apAgent.Agent(configfile)
    agent.Main(sys.argv[1:])
    
    sys.exit(0)

  

