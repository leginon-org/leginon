#!/usr/bin/env python

import os,sys
import optparse
from appionlib import apProject
from appionlib import apStack
from appionlib import apDisplay
from appionlib import proc2dLib
from appionlib import apStackMeanPlot

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--expid', help='expid', type=int)
	parser.add_option('--projectid', help='projectid', type=int)
	parser.add_option('--stackid', help='stackid', type=int)

	options,args = parser.parse_args()
	if len(args) > 0:
		parser.error("Unknown commandline options: " +str(args))
	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")
	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	return params

if __name__=="__main__":
	params = parseOptions()
	apProject.setDBfromProjectId(params['projectid'])

	stackdata = apStack.getOnlyStackData(params['stackid'])
	stackpath = stackdata['path']['path']
	# generate stack if it doesn't exist.
	if not os.path.isdir(stackpath):
		os.makedirs(stackpath)
	fname = os.path.join(stackpath, stackdata['name'])

	# check if stack file already exists
	if os.path.isfile(fname):
		apDisplay.printError("file: '%s' already exists"%fname)
 
	vstackdata = apStack.getVirtualStackParticlesFromId(params['stackid'])
	plist = [int(p['particleNumber'])-1 for p in vstackdata['particles']]

	a = proc2dLib.RunProc2d()
	a.setValue('infile',vstackdata['filename'])
	a.setValue('outfile',fname)
	a.setValue('list',plist)
	a.setValue('apix',apStack.getStackPixelSizeFromStackId(params['stackid']))

	apDisplay.printMsg("generating stack: '%s' with %i particles"%(fname,len(plist)))
	a.run()

	outavg = os.path.join(stackpath, "average.mrc")
	if not os.path.isfile(outavg):
		apStack.averageStack(stack=fname,outfile=outavg)

	montageimg=os.path.join(stackpath,"montage%i.png"%params['stackid'])
	if not os.path.isfile(montageimg):
		apStackMeanPlot.makeStackMeanPlot(params['stackid'],gridpoints=4)

