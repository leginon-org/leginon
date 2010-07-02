#!/usr/bin/env python
"""
Uses EMAN align3d to align 3d models to a reference and average the result
"""

import os
import numpy
#appion
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apFrealign

#=====================
#=====================
class AlignScript(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<param file> ")
		self.parser.add_option("-f", "--file", dest="paramfile", 
			help="Frealign param file, e.g., --file=params.iter008.par", metavar="X")

		self.parser.add_option("-x", "--gracex", dest="gracex", type="int",
			help="X value for Grace output", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['paramfile'] is None:
			apDisplay.printError("Enter a Frealign param file, e.g., --file=params.iter008.pa")
		if not os.path.isfile(self.params['paramfile']):
			apDisplay.printError("File not found: "+self.params['paramfile'])
		self.params['paramfile'] = os.path.abspath(self.params['paramfile'])

	#=====================
	def start(self):
		parttree = apFrealign.parseFrealignParamFile(self.params['paramfile'])
		phases = []
		for partdict in parttree:
			phases.append(partdict['phase_residual'])
		del parttree
		phases.sort()
		phases = numpy.array(phases, dtype=numpy.float32)
		if self.params['gracex'] is None:
			apDisplay.printMsg("xFile:   %s"%(self.params['paramfile']))
			apDisplay.printMsg("xMean:   %.3f +/- %.3f (%d total)"%(phases.mean(), phases.std(), phases.shape[0]))
			apDisplay.printMsg("xRange:  %.2f (min) <> %.2f (0.1) <> %.2f (0.25) <> %.2f (med) <> %.2f (0.75) <> %.2f (0.9) <> %.2f (max)"
				%(phases.min(), phases[int(phases.shape[0]*0.1)], phases[int(phases.shape[0]*0.25)], 
				numpy.median(phases), phases[int(phases.shape[0]*0.75)], phases[int(phases.shape[0]*0.9)], phases.max()))
		else:
			f = open("boxplot.dat", "a")
			#boxplot line: (X, median, upper/lower limit, upper/lower whisker)
			f.write("%d\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\n"
				%(self.params['gracex'], numpy.median(phases), 
				phases[int(phases.shape[0]*0.75)], phases[int(phases.shape[0]*0.25)],
				phases[int(phases.shape[0]*0.9)], phases[int(phases.shape[0]*0.1)],
			))
			f.close()
			f = open("means.dat", "a")
			f.write("%d\t%.8f\n"%(self.params['gracex'], phases.mean()))
			f.close()


#=====================
#=====================
if __name__ == '__main__':
	align = AlignScript()
	align.start()
	align.close()
