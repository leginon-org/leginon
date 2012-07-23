#!/usr/bin/env python

import sys
from appionlib import apConfig
from appionlib import apAgent

if __name__ == '__main__':
	if len(sys.argv) == 1:
		sys.stderr.write("Usage:\n")
		sys.stderr.write(sys.argv[0] + " <options>\n")
		sys.exit(1)
	
	configfile = apConfig.getAppionConfigFile()
	
	agent = apAgent.Agent(configfile)
	agent.Main(sys.argv[1:])
	
	sys.exit(0)

  

