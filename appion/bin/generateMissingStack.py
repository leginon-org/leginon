#!/usr/bin/env python
import sys
import optparse
from appionlib import apProject

from appionlib import apVirtualStack

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--expid', help='expid', type=int)
	parser.add_option('--projectid', help='projectid', type=int)
	parser.add_option('--stackid', help='stackid', type=int)
	# runname and rundir dummy options allow web submission to cluster by creating
	# a place for the job file and log to go.
	parser.add_option('--runname', help='runname dummy', type=str)
	parser.add_option('--rundir', help='rundir dummy', type=str)
	parser.add_option('--jobtype', help='jobtype dummy', type=str)

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

	apVirtualStack.generateMissingStack(params['stackid'])

