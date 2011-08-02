#!/usr/bin/env python

import os
import math
import numpy
import random
import radermacher
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apFile
from appionlib import apEMAN
from appionlib import apImagicFile
from appionlib import apRadon


#=====================
#=====================
class RadonAlign(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--stepsize", dest="stepsize", type="float", default=2,
			help="Angular step size (in degrees) for Radon transform", metavar="#")
		self.parser.add_option("--numrefs", dest="numrefs", type="int", default=10,
			help="Number of references to create", metavar="#")
		self.parser.add_option("--numiter", dest="numiter", type="int", default=20,
			help="Number of iterations", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning of the particles", metavar="#")
		self.parser.add_option("--shiftmax", dest="shiftmax", type="int", default=6,
			help="Maximum amount of x,y shift (in pixels)", metavar="#")
		self.parser.add_option("--shiftstep", dest="shiftstep", type="int", default=2,
			help="Step size of x,y shift (in pixels)", metavar="#")
		self.initreftypes = ('noise', 'average',)
		self.parser.add_option("--initref", dest="initref", default="noise",
			type="choice", choices=self.initreftypes,
			help="Method for reference initialization", metavar="..")
		### default values set later
		self.parser.add_option("--lowpass", dest="lowpass", type="float",
			help="Low pass filter (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", dest="highpass", type="float",
			help="High pass filter (in Angstroms)", metavar="#")
		self.parser.add_option("--maskrad", dest="maskrad", type="int",
			help="Mask radius (in Angstroms)", metavar="#")
		self.parser.add_option("--numpart", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")

		### no default values
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="Stack id to align", metavar="#")


	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("Please provide a user id, e.g. --stackid=15")
		
		if not 'radonshift' in dir(radermacher):
			apDisplay.printError("Radermacher python module is too old, please update")

		boxsize = apStack.getStackBoxsize(self.params['stackid'], msg=False)
		pixelsize = apStack.getStackPixelSizeFromStackId(self.params['stackid'], msg=False)
		numpart = apStack.getNumberStackParticlesFromId(self.params['stackid'], msg=False)

		apDisplay.printMsg("\n\n")
		### get info about the stack
		apDisplay.printMsg("Information about stack id %d"%(self.params['stackid']))
		apDisplay.printMsg("\tboxsize %d pixels"%(boxsize))
		apDisplay.printMsg("\tpixelsize %.3f Angstroms"%(pixelsize))
		apDisplay.printMsg("\tsize %d particles"%(numpart))

		if self.params['maskrad'] is None:
			self.params['pixelmaskrad'] = boxsize/2
			self.params['maskrad'] = self.params['pixelmaskrad']*pixelsize
		else:
			self.params['pixelmaskrad'] = self.params['maskrad']/pixelsize
		if self.params['pixelmaskrad'] > boxsize/2:
			apDisplay.printError("Mask radius larger than boxsize")

		if self.params['numpart'] is None:
			self.params['numpart'] = numpart
		if self.params['numpart'] > numpart:
			apDisplay.printError("Requested more particles than available in stack")
		

	#=====================
	def setRunDir(self):
		"""
		This function is only run, if --rundir is not defined on the commandline
		"""
		### get the path to input stack
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackpath = os.path.abspath(stackdata['path']['path'])
		### go down two directories
		uponepath = os.path.join(stackpath, "..")
		uptwopath = os.path.join(uponepath, "..")
		### add path strings; always add runname to end!!!
		rundir = os.path.join(uptwopath, "align", self.params['runname'])
		### good idea to set absolute path,
		self.params['rundir'] = os.path.abspath(rundir)

	#=====================
	def commitToDatabase(self):
		return

	#=====================
	def start(self):
		"""
		This is the core of your function.
		"""
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		original_stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		filtered_stackfile = os.path.join(self.params['rundir'], self.timestamp+".hed")
		apFile.removeStack(filtered_stackfile, warn=False)
		apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		boxsize = apStack.getStackBoxsize(self.params['stackid'])

		emancmd = "proc2d %s %s apix=%.3f "%(original_stackfile, filtered_stackfile, apix)
		if self.params['lowpass'] is not None:
			emancmd += " lp=%.3f "%(self.params['lowpass'])
		if self.params['highpass'] is not None:
			emancmd += " hp=%.3f "%(self.params['highpass'])
		if self.params['bin'] is not None and self.params['bin'] > 1:
			## determine a multiple of the bin that is divisible by 2 and less than the boxsize
			clipsize = int(math.floor(boxsize/float(self.params['bin']*2)))*2*self.params['bin']
			emancmd += " shrink=%d clip=%d,%d "%(self.params['bin'], clipsize, clipsize)		
		emancmd += " last=%d "%(self.params['numpart']-1)
		apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)

		### confirm that it worked
		if self.params['numpart'] != apFile.numImagesInStack(filtered_stackfile):
			apDisplay.printError("Missing particles in stack")

		### run the radon transform code
		self.radonAlign(filtered_stackfile)
		
		### insert info into database
		self.commitToDatabase()

	#=====================
	def createReferences(self, imagelist):
		if self.params['initref'] == "noise":
			### just fill the references with noise
			reflist = []
			for i in range(self.params['numrefs']):
				shape = imagelist[0].shape
				reflist.append(numpy.random.random(shape))
			return reflist

		elif self.params['initref'] == "average":
			### create empty references for addition
			reflist = []
			for i in range(self.params['numrefs']):
				shape = imagelist[0].shape
				reflist.append(numpy.zeros(shape))

			### shuffle particles into group and average them
			values = range(self.params['numpart'])
			random.shuffle(values)
			i = 0
			partperref = self.params['numpart'] / float(self.params['numrefs'])
			for v in values:
				ref = i % self.params['numrefs']
				reflist[ref] += imagelist[v]/partperref
				i += 1
			return reflist

	#=====================
	def getRadons(self, imagelist):
		try:
			### multiprocessing module is not available in python 2.4
			radonimagelist = apRadon.radonlist(imagelist, stepsize=self.params['stepsize'], maskrad=self.params['pixelmaskrad'])
		except ImportError:
			radonimagelist = apRadon.classicradonlist(imagelist, stepsize=self.params['stepsize'], maskrad=self.params['pixelmaskrad'])
		return radonimagelist

	#=====================
	def radonAlign(self, filtered_stackfile):
		imageinfo = apImagicFile.readImagic(filtered_stackfile)
		imagelist = imageinfo['images']
		reflist = self.createReferences(imagelist)
		apImagicFile.writeImagic(reflist, "reflist00.hed")

		radonreflist = self.getRadons(reflist)
		radonimagelist = self.getRadons(imagelist)


		radoncc = radermacher.radonshift(radonimagelist[0], radonreflist[0], 2)
		for i in range(len(imagelist)):
			bestcc = -1.0
			bestxshift = None
			bestyshift = None
			bestrotangle = None
			bestref = None
			for j in range(len(reflist)):
				for shiftrad in range(0, self.params['shiftmax'], self.params['shiftstep']):
					radonimage = radonimagelist[i]
					radonref = radonreflist[j]
					radoncc = radermacher.radonshift(radonimage, radonref, shiftrad)

					value = radoncc.argmax()
					col = value % radoncc.shape[1] #rotation angle
					row = int(value/radoncc.shape[1]) #shift angle
					cc = radoncc[row,col]
					#print value, col, row, cc

					anglelist = radermacher.getAngles(shiftrad)
					shiftangle = anglelist[col]
					xshift = shiftrad*math.sin(shiftangle)
					yshift = shiftrad*math.cos(shiftangle)
					rotangle = row*self.params['stepsize']

					if cc > bestcc:
						bestcc = cc
						bestxshift = math.ceil(xshift)
						bestyshift = math.ceil(yshift)
						bestrotangle = rotangle
						bestref = j			
						print "%d %d - %.8f - %d %d %.1f"%(i+1,j+1,cc, math.ceil(xshift), math.ceil(yshift), rotangle)
			if i > 2:
				break

		return

#=====================
#=====================
if __name__ == '__main__':
	radonalign = RadonAlign()
	radonalign.start()
	radonalign.close()

