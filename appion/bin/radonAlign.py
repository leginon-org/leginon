#!/usr/bin/env python

import os
import sys
import time
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
from scipy import ndimage
from scipy import stats


#=====================
#=====================
class RadonAlign(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--stepsize", dest="stepsize", type="float", default=2,
			help="Angular step size (in degrees) for Radon transform", metavar="#")
		self.parser.add_option("--numrefs", dest="numrefs", type="int",
			help="Number of references to create", metavar="#")
		self.parser.add_option("--numiter", dest="numiter", type="int", default=20,
			help="Number of iterations", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning of the particles", metavar="#")
		self.parser.add_option("--shiftmax", dest="shiftmax", type="int", default=6,
			help="Maximum amount of x,y shift (in pixels)", metavar="#")
		self.parser.add_option("--shiftstep", dest="shiftstep", type="int", default=2,
			help="Step size of x,y shift (in pixels)", metavar="#")

		### choices
		self.initreftypes = ('noise', 'average',)
		self.parser.add_option("--initref", dest="initref", default="average",
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
		
		if self.params['numrefs'] is None:
			### num refs should go approx. as the sqrt of the number of particles
			self.params['numrefs'] = int(math.ceil(math.sqrt(self.params['numpart'])))+1

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
		shape = imagelist[0].shape
		if self.params['initref'] == "noise":
			### just fill the references with noise
			reflist = []
			for i in range(self.params['numrefs']):
				reflist.append(numpy.random.random(shape))
			return reflist

		elif self.params['initref'] == "average":
			### create empty references for addition
			reflist = []
			for i in range(self.params['numrefs']):
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
			radonimagelist = apRadon.radonlist(imagelist, 
				stepsize=self.params['stepsize'], maskrad=self.params['pixelmaskrad'])
		except ImportError:
			radonimagelist = apRadon.classicradonlist(imagelist, 
				stepsize=self.params['stepsize'], maskrad=self.params['pixelmaskrad'])
		return radonimagelist

	#=====================
	def getBestAlignForImage(self, image, radonimage, reflist, radonreflist, oldshift):
		aligndata = {}
		aligndata['bestcc'] = -1.0
		for j in range(len(reflist)):
			for shiftrad in range(0, self.params['shiftmax'], self.params['shiftstep']):
				radonimage
				radonref = radonreflist[j]
				radoncc = radermacher.radonshift(radonimage, radonref, shiftrad)

				value = radoncc.argmax()
				### FUTURE: use peakfinder to get subpixel peak
				col = value % radoncc.shape[1] #rotation angle
				row = int(value/radoncc.shape[1]) #shift angle
				cc = radoncc[row,col]
				#print value, col, row, cc

				if cc > aligndata['bestcc']:
					### calculate parameters
					### FUTURE: get shift list rather than angle list
					anglelist = radermacher.getAngles(shiftrad)
					shiftangle = anglelist[col]
					xshift = shiftrad*math.sin(shiftangle)
					yshift = shiftrad*math.cos(shiftangle)
					rotangle = row*self.params['stepsize']

					### save values
					aligndata['bestcc'] = cc
					aligndata['xshift'] = math.ceil(xshift)
					aligndata['yshift'] = math.ceil(yshift)
					aligndata['rotangle'] = rotangle
					aligndata['refid'] = j
		#print ("ref %02d | %.8f | x %2d y %2d ang %.1f"
		#	%(aligndata['refid'],aligndata['bestcc'], aligndata['xshift'], 
		#	aligndata['yshift'], aligndata['rotangle']))
		if oldshift is not None:
			aligndata['xshift'] += oldshift['xshift']
			aligndata['yshift'] += oldshift['yshift']
		return aligndata

	#=====================
	def transformImage(self, image, aligndata, refimage):
		alignedimage = image
		shift = (aligndata['xshift'], aligndata['yshift'])
		alignedimage = ndimage.shift(alignedimage, shift=shift, mode='wrap', order=1)
		### due to the nature of Radon shifts, it cannot tell the difference between 0 and 180 degrees
		alignedimage1 = ndimage.rotate(alignedimage, -aligndata['rotangle'], reshape=False, order=1)
		alignedimage2 = ndimage.rotate(alignedimage, -aligndata['rotangle']+180, reshape=False, order=1)
		cc1 = self.getCCValue(alignedimage1, refimage)
		cc2 = self.getCCValue(alignedimage2, refimage)
		if cc1 > cc2:
			return alignedimage1
		else:
			return alignedimage2

	#=====================
	def getCCValue(self, imgarray1, imgarray2):
		### faster cc, thanks Jim
		ccs = stats.pearsonr(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
		return ccs[0]

	#=====================
	def radonAlign(self, stackfile):
		"""
		performs the meat of the program aligning the particles and creating references
		"""
		### FUTURE: only read a few particles into memory at one time
		imageinfo = apImagicFile.readImagic(stackfile, msg=False)
		imagelist = imageinfo['images']
		reflist = self.createReferences(imagelist)
		radonimagelist = self.getRadons(imagelist)
		
		### a pre-normalization value so the reference pixels do not overflow
		partperref = self.params['numpart'] / float(self.params['numrefs'])
		
		for iternum in range(self.params['numiter']):
			### save references to a file
			apImagicFile.writeImagic(reflist, "reflist%02d.hed"%(iternum), msg=False)
		
			### create Radon transforms for references
			radonreflist = self.getRadons(reflist)
		
			### create empty references
			newreflist = []
			newrefcount = []
			shape = imagelist[0].shape
			for i in range(self.params['numrefs']):
				newrefcount.append(0)
				newreflist.append(numpy.zeros(shape))

			### get alignment parameters
			aligndatalist = []
			cclist = []
			t0 = time.time()
			for i in range(len(imagelist)):
				if i % 50 == 0:
					### FUTURE: add time estimate
					sys.stderr.write(".")
				image = imagelist[i]
				radonimage = radonimagelist[i]
				aligndata = self.getBestAlignForImage(image, radonimage, reflist, radonreflist, None)
				#aligndatalist.append(aligndata)
				refid = aligndata['refid']
				cclist.append(aligndata['bestcc'])

				### create new references
				refimage = reflist[refid]
				alignedimage = self.transformImage(image, aligndata, refimage)
				newreflist[refid] += alignedimage/partperref
				newrefcount[refid] += 1
			sys.stderr.write("\n")
			print "Alignment complete in %s"%(apDisplay.timeString(time.time()-t0))

			### report median cross-correlation, it should get better each iter
			mediancc = numpy.median(numpy.array(cclist))
			apDisplay.printMsg("Iter %02d, Median CC: %.8f"%(iternum, mediancc))
			print newrefcount

			### FUTURE: re-calculate Radon transform for particles with large shift

			### new references are now the old references
			shape = reflist[0].shape
			reflist = []
			for i in range(self.params['numrefs']):
				if newrefcount[i] == 0:
					### reference with no particles -- just add noise
					apDisplay.printWarning("Reference %02d has no particles"%(i+1))
					ref = numpy.random.random(shape)
				else:
					ref = (newreflist[i] / newrefcount[i]) * partperref
				reflist.append(ref)

		return aligndatalist

#=====================
#=====================
if __name__ == '__main__':
	radonalign = RadonAlign()
	radonalign.start()
	radonalign.close()

