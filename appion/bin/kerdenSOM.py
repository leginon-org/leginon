#!/usr/bin/env python

"""
Kernel Probability Density Estimator Self-Organizing Map
"""
# python
import os
import subprocess
import glob
# appion
import appionScript
import apXmipp
import apDisplay
import appionData
import apEMAN


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
		proc = subprocess.Popen(kerdencmd, shell=True)
		proc.wait()

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
		files = glob.glob(self.timestamp+".[0-9]*")
		files.sort(self.sortFile)
		montagecmd = ("montage -geometry +4+4 -tile %dx%d "%(self.params['xdim'], self.params['ydim']))
		for fname in files:
			emancmd = ("proc2d %s %s list=%s average"%
				(self.instack, fname+".png", fname))
			apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=False)
			montagecmd += fname+".png "
		montagecmd += "montage.png"
		apEMAN.executeEmanCmd(montagecmd, showcmd=True, verbose=False)

	#======================
	def start(self):
		apDisplay.printMsg("Hey this works")
		aligndata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		boxsize = aligndata['boxsize']
		apix = aligndata['pixelsize']
		maskpixrad = self.params['maskrad']/apix
		self.instack = os.path.join(aligndata['path']['path'], aligndata['imagicfile'])
		outdata = "stack.data"

		apXmipp.convertStackToXmippData(self.instack, outdata, maskpixrad, boxsize, numpart=None)
		self.runKerdenSOM(outdata)
		self.convertfiles()

#======================
#======================
if __name__ == '__main__':
	kerdenSOM = kerdenSOMScript()
	kerdenSOM.start()
	kerdenSOM.close()

