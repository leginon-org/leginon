#!/usr/bin/env python

import os
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apStackMeanPlot

def generateMissingStack(stackid):
	# appion database must be set before running this
	stackdata = apStack.getOnlyStackData(stackid)
	stackpath = stackdata['path']['path']
	# generate stack if it doesn't exist.
	if not os.path.isdir(stackpath):
		os.makedirs(stackpath)
	fname = os.path.join(stackpath, stackdata['name'])

	# check if stack file already exists
	if os.path.isfile(fname):
		apDisplay.printError("file: '%s' already exists"%fname)

	vstackdata = apStack.getVirtualStackParticlesFromId(stackid)
	#appion numbering starts at 1
	plist = [int(p['particleNumber']) for p in vstackdata['particles']]

	apDisplay.printMsg("generating stack: '%s' with %i particles"%(fname,len(plist)))
	apStack.makeNewStack(vstackdata['filename'], fname, plist)

	outavg = os.path.join(stackpath, "average.mrc")
	if not os.path.isfile(outavg):
		apStack.averageStack(stack=fname,outfile=outavg)

	montageimg=os.path.join(stackpath,"montage%i.png"% stackid)
	if not os.path.isfile(montageimg):
		apStackMeanPlot.makeStackMeanPlot(stackid,gridpoints=4)

