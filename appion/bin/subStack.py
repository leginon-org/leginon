#!/usr/bin/python -O

#python
import os
import sys
from optparse import OptionParser
#appion
import apStack
import shutil
import apDisplay
import apParam
import apUpload
import apDB
import appionData

appiondb=apDB.apdb


def parseCommandLine():
	usage = "Usage: %prog --old-stack-id=ID --keep-file=FILE [options]"
	parser = OptionParser(usage=usage)

	parser.add_option("-s", "--old-stack-id", dest="stackid", type="int",
		help="Stack database id", metavar="ID")
	parser.add_option("-k", "--keep-file", dest="keepfile",
		help="File listing which particles to keep", metavar="FILE")
	parser.add_option("--commit", dest="commit", default=True,
		action="store_true", help="Commit stack to database")
	parser.add_option("--no-commit", dest="commit", default=True,
		action="store_false", help="Do not commit stack to database")
	parser.add_option("-o", "--outdir", dest="outdir",
		help="Output directory", metavar="PATH")
	parser.add_option("-d", "--description", dest="description", default="",
		help="Stack description", metavar="TEXT")
	parser.add_option("-n", "--new-stack-name", dest="runname",
		help="Run id name", metavar="STR")

	params = apParam.convertParserToParams(parser)
	return params

#--------
def checkConflicts(params):
	if params['stackid'] is None:
		apDisplay.printError("stackid was not defined")
	if params['description'] is None:
		apDisplay.printError("stack description was not defined")
	if params['runname'] is None:
		apDisplay.printError("new stack name was not defined")
	if params['keepfile'] is None:
		apDisplay.printError("keep file was not defined")
	params['keepfile'] = os.path.abspath(params['keepfile'])
	if not os.path.isfile(params['keepfile']):
		apDisplay.printError("Could not find keep file: "+params['keepfile'])


#-----------------------------------------------------------------------

if __name__ == '__main__':
	#read command line
	params = parseCommandLine()
	checkConflicts(params)

	#get stack data
	stackdata = apStack.getOnlyStackData(params['stackid'])
	oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])

	#create run directory
	if params['outdir'] is None:
		path = stackdata['path']['path']
		path = os.path.split(os.path.abspath(path))[0]
		params['outdir'] = path
	params['rundir'] = os.path.join(params['outdir'], params['runname'])
	apParam.createDirectory(params['rundir'])
	apDisplay.printMsg("Run directory: "+params['rundir'])
	os.chdir(params['rundir'])
	if not os.path.isfile(os.path.basename(params['keepfile'])):
		shutil.copy(params['keepfile'], os.path.basename(params['keepfile']))

	#new stack path
	newstack = os.path.join(params['rundir'], stackdata['name'])
	apStack.checkForPreviousStack(newstack)

	#get number of particles
	f = open(params['keepfile'], "r")
	numparticles = len(f.readlines())
	f.close()
	params['description'] += (
		(" ... substack of %d particles from original stackid=%d" 
		% (numparticles, params['stackid']))
	)
	
	#create the new sub stack
	apStack.makeNewStack(oldstack, newstack, params['keepfile'])

	apStack.commitSubStack(params)
	apStack.averageStack(stack=newstack)

