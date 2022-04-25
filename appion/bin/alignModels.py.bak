#!/usr/bin/env python
"""
Uses EMAN align3d to align 3d models to a reference and average the result
"""

import os
import glob
import numpy
#appion
from appionlib import basicScript
from appionlib import apThread
from appionlib import apVolume
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apEMAN
from pyami import mrc, imagefun

#=====================
#=====================
class AlignScript(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --reference=<mrc file> --average=average.mrc --volumes=*.mrc ")
		self.parser.add_option("--reference", dest="reference", 
			help="3d MRC reference file", metavar="X")
		self.parser.add_option("--average", dest="average", default="average-volume.mrc",
			help="average volume will be saved to this 3d MRC file", metavar="X")
		self.parser.add_option("--volumes", dest="volumes", 
			help="wildcard pointing to volumes to align", metavar="X")

		### EMAN align3d options, see http://blake.bcm.tmc.edu/eman/eman1/progs/align3d.html
		self.parser.add_option("--slow", dest="slow", default=False,
			action="store_true", help="For models that seem to be difficult to align, this will search with a finer angular step")

		self.parser.add_option("--noshrink", dest="noshrink", default=False,
			action="store_true", help="Normally the models are scaled down by a factor of 2 for faster alignment. This causes the full sized model to be used.")

	#=====================
	def checkConflicts(self):
		if self.params['reference'] is None:
			apDisplay.printError("Enter a reference file name, e.g. --reference=reference.mrc")
		if not os.path.isfile(self.params['reference']):
			apDisplay.printError("File not found: "+self.params['reference'])
		self.params['reference'] = os.path.abspath(self.params['reference'])

		if self.params['volumes'] is None:
			apDisplay.printError("Enter a volumes wildcard, e.g. --reference=volume*.mrc")

	#=====================
	def start(self):
		### get volume files
		volumefiles = glob.glob(self.params['volumes'])
		if not volumefiles:
			apDisplay.printError("Could not find volumes, %s"%(self.params['volumes']))

		### make list of all alignments to run
		cmdlist = []
		alignfiles = []
		for volfile in volumefiles:
			alignfile = "align-"+os.path.basename(volfile)
			alignfiles.append(alignfile)
			emancmd = "align3d %s %s %s "%(self.params['reference'], volfile, alignfile)
			if self.params['slow'] is True:
				emancmd += "slow "
			if self.params['noshrink'] is True:
				emancmd += "noshrink "
			#print emancmd
			cmdlist.append(emancmd)

		### run several alignment commands in parallel
		apThread.threadCommands(cmdlist)

		### average volumes together
		ref = mrc.read(self.params['reference'])
		average = numpy.zeros(ref.shape, dtype=numpy.float32)
		del ref
		count = 0
		for alignfile in alignfiles:
			if not os.path.isfile(alignfile):
				apDisplay.printWarning("aligned volume not found: %s"%(alignfile))
			aligned = mrc.read(alignfile)
			count += 1
			### this assume all aligned volume have same box size
			average += aligned
			del aligned

		### save average
		average /= count
		avgfile = os.path.abspath(self.params['average'])
		mrc.write(average, avgfile)
		apDisplay.printMsg("Wrote average file: "+avgfile)
		
#=====================
#=====================
if __name__ == '__main__':
	align = AlignScript()
	align.start()
	align.close()
