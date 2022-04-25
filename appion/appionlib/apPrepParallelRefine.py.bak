#!/usr/bin/env python

import sys
import os
from optparse import OptionParser

class PrepParallelRefinement(object):
	def __init__(self):
		self.params = {}
		self.parser = OptionParser()
		self.setupParserOptions()
		self.params = self.convertParserToParams()
		os.chdir(self.params['recondir'])

	def setupParserOptions(self):
		self.parser.add_option("--ppn", dest="ppn", type="int",
			help="processers per node", default=1, metavar="###")
		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="total number of processers to be used", default=1, metavar="###")
		self.parser.add_option("--recondir", dest="recondir", default='./',
			help="Base path for the processing, e.g. --recondir=/home/you/rundir/recon", metavar="PATH")

	def convertParserToParams(self):
		parser = self.parser
		parser.disable_interspersed_args()
		(options, args) = parser.parse_args()
		if len(args) > 0:
			sys.exit("Unknown commandline options: "+str(args))
		if len(sys.argv) < 2:
			parser.print_help()
			parser.error("no options defined")

		params = {}
		for i in parser.option_list:
			if isinstance(i.dest, str):
				params[i.dest] = getattr(options, i.dest)
		return params

	def setupRefineScript(self):
		'''
		Not implemented Yet
		'''
		print 'setupRefineScript need to be implemented in the subclasses'

	def run(self):
		self.setupRefineScript()

if __name__ == '__main__':
	app = PrepParallelRefinement()
	app.run()

