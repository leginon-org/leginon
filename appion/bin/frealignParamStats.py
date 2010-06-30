#!/usr/bin/env python
"""
Uses EMAN align3d to align 3d models to a reference and average the result
"""

import os
import re
import sys
#appion
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apFile


#=====================
#=====================
class AlignScript(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<param file> ")
		self.parser.add_option("--file", dest="paramfile", 
			help="Frealign param file, e.g., --file=params.iter008.par", metavar="X")

		self.parser.add_option("--slow", dest="slow", default=False,
			action="store_true", help="For mo")

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
		eulerfiles = []
		alignfiles = []
		if not os.path.isdir("align"):
			os.mkdir("align")
		for volfile in volumefiles:
			alignfile = "align/align-"+os.path.basename(volfile)
			#alignfile = "/dev/null"
			eulerfile = "align/euler-"+os.path.basename(volfile)+".txt"
			alignfiles.append(alignfile)
			eulerfiles.append(eulerfile)

			emancmd = "align3d %s %s %s "%(self.params['reference'], volfile, alignfile)
			if self.params['slow'] is True:
				emancmd += "slow "
			if self.params['noshrink'] is True:
				emancmd += "noshrink "
			if self.params['trans'] is True:
				emancmd += "trans "
			emancmd += "> "+eulerfile

			#print emancmd
			cmdlist.append(emancmd)

		### run several alignment commands in parallel
		#apThread.threadCommands(cmdlist, pausetime=10)

		### read euler files
		#alignfiles = []
		cmdlist = []
		eulerf = open("eulersummary.txt", "w")
		for eulerfile in eulerfiles:
			if not os.path.isfile(eulerfile):
				apDisplay.printWarning("aligned volume euler not found: %s"%(eulerfile))
				continue
			f = open(eulerfile)
			lines = f.readlines()
			eulerline = lines[-1]
			#print eulerline.strip()
			result = re.search("r: ([0-9\.]+) ([0-9\.]+) ([0-9\.]+)$", eulerline)
			if not result or not result.groups():
				continue
			#print result.groups()

			alt = float(result.groups()[1])
			az  = float(result.groups()[2])
			phi = float(result.groups()[0])

			eulerf.write("%.4f,%.4f,%.4f,%s\n"%(alt, az, phi, eulerfile))

			#emancmd = "proc3d %s %s rot=%.4f,%.4f,%.4f"%(invol, outvol, alt, az, phi)

			#cmdlist.append(emancmd)
		eulerf.close()
		#return

		### run several alignment commands in parallel
		#apThread.threadCommands(cmdlist[:8])

		### average volumes together
		ref = mrc.read(self.params['reference'])
		average = numpy.zeros(ref.shape, dtype=numpy.float32)
		count = 0
		edgemap = imagefun.filled_sphere(ref.shape, ref.shape[0]/4.0-1.0)
		spheremap = numpy.abs(edgemap - 1)
		spheremap = ndimage.shift(spheremap, numpy.array(ref.shape)/2.0)
		for alignfile in alignfiles:
			if not os.path.isfile(alignfile):
				apDisplay.printWarning("aligned volume not found: %s"%(alignfile))
			aligned = mrc.read(alignfile)
			pcim = correlator.cross_correlate(ref, aligned)
			pcim = numpy.where(pcim<0.0, 0.0, pcim)
			mrc.write(pcim*spheremap, "pcim%03d.mrc"%(count))
			peak = getPixelPeak3D(pcim*spheremap)
			print peak
			aligned = ndimage.shift(aligned, peak, mode='wrap')
			count += 1
			### this assume all aligned volume have same box size
			average += aligned
			mrc.write(aligned, "test%03d.mrc"%(count))
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
