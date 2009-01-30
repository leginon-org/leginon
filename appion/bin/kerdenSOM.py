#!/usr/bin/env python

"""
Kernel Probability Density Estimator Self-Organizing Map
"""
# python
import os
import sys
import subprocess
import glob
import time
import shutil
# appion
import appionScript
import apXmipp
import apDisplay
import appionData
import apEMAN
import apFile


#======================
#======================
class kerdenSOMScript(appionScript.AppionScript):
	#======================
	def setupParserOptions(self):
		self.parser.add_option("-a", "--alignid", dest="alignstackid", type="int", 
			help="Alignment stack id", metavar="#")
		self.parser.add_option("-m", "--maskrad", dest="maskrad", type="float", 
			help="Mask radius in Angstroms", metavar="#")
		self.parser.add_option("-x", "--xdim", dest="xdim", type="int", 
			help="X dimension", metavar="#")
		self.parser.add_option("-y", "--ydim", dest="ydim", type="int", 
			help="Y dimension", metavar="#")
		self.parser.add_option("--numpart", dest="numpart", type="int", 
			help="Number of particles, default all in stack", metavar="#")
		self.convergemodes = ( "normal", "fast", "slow" )
		self.parser.add_option("--converge", dest="converge",
			help="Convergence criteria mode", metavar="MODE", 
			type="choice", choices=self.convergemodes, default="normal" )

	#======================
	def checkConflicts(self):
		if self.params['alignstackid'] is None:
			apDisplay.printError("Please enter an aligned stack id, e.g. --alignstackid=4")

	#======================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#======================
	def runKerdenSOM(self, indata):
		"""
		From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/KerDenSOM

		KerDenSOM stands for "Kernel Probability Density Estimator Self-Organizing Map".
		It maps a set of high dimensional input vectors into a two-dimensional grid.
		"""
		apDisplay.printMsg("Running KerDen SOM")
		outstamp = os.path.join(self.params['rundir'], self.timestamp)
		kerdencmd = ( "xmipp_classify_kerdensom -i %s -o %s -xdim %d -ydim %d -saveclusters "%
			(indata, outstamp, self.params['xdim'], self.params['ydim'])
		)
		### convergence criteria
		if self.params['converge'] == "fast":
			kerdencmd += " -eps 1e-5 "
		elif self.params['converge'] == "slow":
			kerdencmd += " -eps 1e-9 "
		else:
			kerdencmd += " -eps 1e-7 "

		apDisplay.printColor(kerdencmd, "cyan")
		proc = subprocess.Popen(kerdencmd, shell=True)
		proc.wait()
		time.sleep(1)
		return

	#======================
	def fileId(self, fname):
		ext = os.path.splitext(fname)[1]
		num = int(ext[1:])
		return num

	#======================
	def sortFile(self, a, b):
		if self.fileId(a) > self.fileId(b):
			return 1
		return -1

	#======================
	def convertfiles(self):
		apDisplay.printMsg("Converting files")

		### create crappy files
		emancmd = ( "proc2d "+self.instack+" crap.mrc first=0 last=0 mask=1" )
		apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)
		emancmd = ( "proc2d crap.mrc crap.png" )
		apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)

		files = glob.glob(self.timestamp+".[0-9]*")
		files.sort(self.sortFile)
		montagecmd = ("montage -geometry +4+4 -tile %dx%d "%(self.params['xdim'], self.params['ydim']))
		stackname = "kerden.hed"
		count = 0
		for listname in files:
			if not os.path.isfile(listname) or apFile.fileSize(listname) < 1:
				### create a ghost particle
				emancmd = ( "proc2d crap.mrc "+stackname+" " )
				sys.stderr.write("skipping "+listname+"\n")
				apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)
				### create png
				shutil.copy("crap.png", listname+".png")
			else:
				### average particles
				emancmd = ("proc2d %s %s list=%s average"%
					(self.instack, stackname, listname))
				apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=False)
				### create png
				emancmd = ("proc2d %s %s first=%d last=%d"%
					(stackname, listname+".png", count, count))
				apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)
			montagecmd += listname+".png "
			count +=1
		montagecmd += "montage.png"
		apEMAN.executeEmanCmd(montagecmd, showcmd=True, verbose=False)

	#======================
	def start(self):
		apDisplay.printMsg("Hey this works")
		aligndata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		boxsize = aligndata['boxsize']
		apix = aligndata['pixelsize']
		maskpixrad = self.params['maskrad']/apix
		if maskpixrad*2 > boxsize-2:
			apDisplay.printError("Mask radius is too big for boxsize: %d > %d"%(maskpixrad*2,boxsize-2))
		apDisplay.printMsg("Mask radius and boxsize: %.1f < %d"%(maskpixrad*2,boxsize-2))
		self.instack = os.path.join(aligndata['path']['path'], aligndata['imagicfile'])
		outdata = "stack.data"

		apXmipp.convertStackToXmippData(self.instack, outdata, maskpixrad, 
			boxsize, numpart=self.params['numpart'])

		self.runKerdenSOM(outdata)
		self.convertfiles()

#======================
#======================
if __name__ == '__main__':
	kerdenSOM = kerdenSOMScript()
	kerdenSOM.start()
	kerdenSOM.close()

