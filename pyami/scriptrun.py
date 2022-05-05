#!/usr/bin/env python
import sys
import os

class ScriptRun(object):
	'''
	Base class for script run with option parsing.
	'''
	def __init__(self):
		self.is_win32 = sys.platform == 'win32'
		self.params = self.parseParams()

	def parseParams(self):
		'''
		Use OptionParser to get parameters
		'''
		parser = self._createParser()
		self.setOptions(parser)
		# parsing options
		(options, optargs) = parser.parse_args(sys.argv[1:])
		if len(optargs) > 0:
			print("Unknown commandline options: "+str(optargs))
		if not self.use_gui and len(sys.argv) < 2:
			parser.print_help()
			sys.exit()
		params = {}
		for i in parser.option_list:
			if isinstance(i.dest, str):
				params[i.dest] = getattr(options, i.dest)
		self.checkOptionConflicts(params)
		return params

	def _createParser(self):
		if len(sys.argv) == 1 and self.is_win32:
			try:
				from optparse_gui import OptionParser
				self.use_gui = True
			except:
				raw_input('Need opparse_gui to enter options on Windows')
				sys.exit()
		else:
			from optparse import OptionParser
			self.use_gui = False
		parser = OptionParser()
		return parser

	def setOptions(self, parser):
		"""set options in parser"""
		raise NotImplemented

	def checkOptionConflicts(self,params):
		"""check conflicts before run"""
		pass
	
	def getAndValidatePath(self,key):
		pathvalue = self.params[key]
		if pathvalue and not os.access(pathvalue, os.R_OK):
			sys.stderr.write('%s not exists or not readable\n' % (pathvalue,))
			sys.exit(1)
		return pathvalue

