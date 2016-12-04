#!/usr/bin/env python

import os
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apAlignment
from appionlib import appiondata

#=====================
class GetAlignShift(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--aid", dest="alignstackid", type="int",
			help="An align stack id ", metavar="#")

	#=====================
	def checkConflicts(self):
		"""
		conflict checking
		"""
		self.alignstack = appiondata.ApAlignStackData().direct_query(self.params['alignstackid'])
		if not self.isAlignStackId(self.alignstack):
			apDisplay.printError("No alignment params found. Invaid alignstack id")

	#=====================
	def isAlignStackId(self, alignstack):
		"""
		"""
		alignrun = alignstack['alignrun']
		if apAlignment.getAlignPackage(alignrun):
			return True
		else:
			return False

	#=====================
	def setRunDir(self):
		"""
		This function is only run, if --rundir is not defined on the commandline

		This function decides when the results will be stored. You can do some complicated
		things to set a directory.

		"""
		rundir = './'
		### good idea to set absolute path,
		### cleans up 'path/stack/stack1/../../example/ex1' -> 'path/example/ex1'
		self.params['rundir'] = os.path.abspath(rundir)
		"""
		In all cases, we set the value for self.params['rundir']
		"""

	#=====================
	def start(self):
		"""
		This is the core of your function.
		You decide what happens here!
		"""
		outfile = os.path.join(self.params['rundir'],'partshift.txt')
		out = open(outfile,'w')
		out.write('\t'.join(['part_number','x','y'])+'\n')
		### get info about the stack
		
		package = apAlignment.getAlignPackage(self.alignstack['alignrun'])
		aptcls = appiondata.ApAlignParticleData(alignstack=self.alignstack).query()
		aptcls.reverse()
		apDisplay.printMsg('got %d align particles' % len(aptcls))

		for p in aptcls:
			xydict = apAlignment.getAlignShift(p, package)
			line = '%d\t%.2f\t%.2f\n'% (p['partnum'],xydict['x'],xydict['y'])
			out.write(line)
		out.close()
		apDisplay.printMsg('Result saved to: %s' % outfile)

#=====================
#=====================
if __name__ == '__main__':
	examplescript = GetAlignShift()
	examplescript.start()
	examplescript.close()

