#!/usr/bin/python -O

#python
import os
import sys
from optparse import OptionParser
#appion
import apStack
import apDisplay
import apParam


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
	parser.add_option("-n", "--new-stack-name", dest="runname",
		help="Run id name", metavar="STR")

	params = apParam.convertParserToParams(parser)
	return params

#--------
def checkConflicts(params):
	if params['stackid'] is None:
		apDisplay.printError("stackid was not defined")
	if params['keepfile'] is None:
		apDisplay.printError("keep file was not defined")
	if params['keepfile'] is None:
		apDisplay.printError("run id name was not defined")
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
	stackpath = os.path.join(stackdata['path']['path'], stackdata['name'])

	#get number of particles
	f.open(params['keepfile'], "r")
	numparticles = len(f.readlines())
	f.close()
	params['description'] = (
		origdescription+
		(" ... substack of %d particles from original stackid=%d" 
		% (numparticles, params['stackid']))
	)

	#do something
	print stackpath
	for i in stackdata:
		print i
		break

	apStack.makeNewStack()



