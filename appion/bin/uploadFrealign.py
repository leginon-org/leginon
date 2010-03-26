#!/usr/bin/env python

#python
import os
import re
import sys
import time
import math
import subprocess
#appion
from appionlib import appionScript
from appionlib import apEMAN
from appionlib import apDisplay
from appionlib import apChimera
from appionlib import apEulerJump


class UploadFrealign(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --commit --description='<text>' [options]")
		### ints
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="#")
		self.parser.add_option("--mass", dest="mass", type="int",
			help="Particle mass in kDa for Chimera snapshots (optional)", metavar="#")

		### floats
		self.parser.add_option("--zoom", dest="zoom", type="float", default=1.0, 
			help="Zoom factor for Chimera snapshots (optional)", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['mass'] is None:
			apDisplay.printError("Please provide an estimate for the mass (in kDa), e.g. --mass=782")

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#=====================
	def parseFrealignParamFile(self, paramfile):
		"""
		parse a typical FREALIGN parameter file from v8.08
		"""
		if not os.path.isfile(paramfile):
			apDisplay.printError("Parameter file does not exist: %s"%(paramfile))

		### cannot assume spaces will separate columns.
		#0000000001111111111222222222233333333334444444444555555555566666666667777777777888888888899999999990000000000
		#1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
		#     24  219.73   84.00  299.39   15.33  -17.51  10000.     1  27923.7  27923.7  -11.41   0.00    0.00
		f = open(paramfile, "r")
		parttree = []
		apDisplay.printMsg("Processing parameter file: %s"%(paramfile))
		for line in f:
			sline = line.strip()
			if sline[0] == "C":
				### comment line
				continue
			partdict = {
				'partnum': int(line[0:7].strip()),
				'euler1': float(line[8:15]),
				'euler2': float(line[16:23]),
				'euler3': float(line[24:31]),
				'xshift': float(line[32:39]),
				'yshift': float(line[40:47]),
				'phaseres': float(line[88:94]),
			}
			parttree.append(partdict)
		f.close()
		apDisplay.printMsg("Processed %d particles"%(len(parttree)))
		return parttree
			
	#=====================
	def checkResults(self):
		if not os.path.isfile("params.iter001.par"):
			### we do not have results
			if os.path.isfile("results.tgz"):
				### the results are still zipped
				apDisplay.printMsg("Unzipping Frealign results...")
				cmd = "tar -xzf results.tgz"
				proc = subprocess.Popen(cmd, shell=True)
				proc.wait()
			else:
				apDisplay.printError("Could not find Frealign results...")
		return

	#=====================
	def processFrealignVolume(self, iternum):
		apix = 1.04

		volumeImagicFile = os.path.join(self.params['rundir'], "iter%03d.hed"%(iternum))
		volumeMrcFile = os.path.join(self.params['rundir'], "iter%03d.mrc"%(iternum))
		if not os.path.isfile(volumeMrcFile):
			emancmd = "proc3d %s %s apix=%.3f origin=0,0,0 norm=0,1"%(volumeImagicFile, volumeMrcFile, apix)
			apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)
		if not os.path.isfile(volumeMrcFile):
			apDisplay.printError("Failed to convert volume")

		apChimera.filterAndChimera(volumeMrcFile, res=10, apix=apix, chimtype='snapshot',
			contour=1.0, zoom=self.params['zoom'], sym='c7', silhouette=True, mass=self.params['mass'])

		return volumeMrcFile

	#=====================
	def uploadIteration(self, iternum):
		volumeMrcFile = self.processFrealignVolume(iternum)

		paramfile = "params.iter%03d.par"%(iternum)
		parttree = self.parseFrealignParamFile(paramfile)

	#=====================
	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		self.checkResults()
		numiter = 3
		for i in range(numiter):
			apDisplay.printColor("\nUploading iteration %d of %d\n"%(i+1, numiter), "green")

			self.uploadIteration(i+1)

		#apDisplay.printMsg("calculating euler jumpers for recon="+str(reconrunid))
		#eulerjump = apEulerJump.ApEulerJump()
		#eulerjump.calculateEulerJumpsForEntireRecon(reconrunid, stackid)
		#apRecon.getGoodBadParticlesFromReconId(reconrunid)

if __name__ == '__main__':
	upfrealign = UploadFrealign()
	upfrealign.start()
	upfrealign.close()
