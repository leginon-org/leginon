#!/usr/bin/env python

import os
from appionlib import apStack
from appionlib import apDisplay
from appionlib import proc2dLib
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
	plist = [int(p['particleNumber'])-1 for p in vstackdata['particles']]

	a = proc2dLib.RunProc2d()
	a.setValue('infile',vstackdata['filename'])
	a.setValue('outfile',fname)
	a.setValue('list',plist)
	a.setValue('apix',apStack.getStackPixelSizeFromStackId(stackid))

	apDisplay.printMsg("generating stack: '%s' with %i particles"%(fname,len(plist)))
	a.run()

	outavg = os.path.join(stackpath, "average.mrc")
	if not os.path.isfile(outavg):
		apStack.averageStack(stack=fname,outfile=outavg)

	montageimg=os.path.join(stackpath,"montage%i.png"% stackid)
	if not os.path.isfile(montageimg):
		apStackMeanPlot.makeStackMeanPlot(stackid,gridpoints=4)

