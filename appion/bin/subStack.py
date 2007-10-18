#!/usr/bin/python -O

#python
import os
import sys
from optparse import OptionParser
#appion
import apStack
import apDisplay

def parseCommandLine():
	usage = "Usage: %prog --stackid=ID --keep-file=FILE [options]"
	parser = OptionParser(usage=usage)
	parser.add_option("-s", "--stackid", dest="stackid", type="int",
		help="Stack database id", metavar="ID")
	parser.add_option("-k", "--keep-file", dest="keepfile",
		help="File listing which particles to keep", metavar="FILE")
	parser.add_option("--commit", dest="commit", default=True,
		action="store_true", help="Commit stack to database")
	parser.add_option("--no-commit", dest="commit", default=True,
		action="store_false", help="Do not commit stack to database")
	parser.disable_interspersed_args()
	(options, args) = parser.parse_args()

	if len(args) > 0:
		apDisplay.printError("Unknown commandline options: "+str(args))
	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")

	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	return params

#--------
def checkConflicts(params):
	if params['stackid'] is None:
		apDisplay.printError("stackid was not defined")
	if params['keepfile'] is None:
		apDisplay.printError("keep file was not defined")
	params['keepfile'] = os.path.abspath(params['keepfile'])
	if not os.path.isfile(params['keepfile']):
		apDisplay.printError("Could not find keep file: "+params['keepfile'])

#-----------------------------------------------------------------------

if __name__ == '__main__':
	params = parseCommandLine()
	checkConflicts(params)

	stackdata = apStack.getStackFromId(params['stackid'])
	print len(stackdata)
	for i in stackdata:
		print i
		break





