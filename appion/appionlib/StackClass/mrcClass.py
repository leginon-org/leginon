#!/usr/bin/env python

import os
from pyami import mrc
from appionlib import apDisplay
from appionlib.StackClass import baseClass

class MrcClass(baseClass.StackClass):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def readHeader(self):
		# read the header information
		#  or initialize empty stack
		# required variables to set are below
		if os.path.isfile(self.filename) and self.fileSize() > 1:
			self.mrcheader = mrc.readHeaderFromFile(self.filename)
			self.boxsize = self.mrcheader['nx']
			self.apix = self.getPixelSize()
			self.originalNumberOfParticles = self.mrcheader['nz']
	def newFile(self):
		# create new file to append to
		raise NotImplementedError
	def updatePixelSize(self):
		# create new file to append to
		raise NotImplementedError	
	def readParticles(self, particleNumbers):
		# read a list of particles into memory
		raise NotImplementedError
	def appendParticlesToFile(self, particleDataTree):
		# takes a list of 2D numpy arrays
		#  and wrtie them to a file
		if os.path.exists(self.filename):
			partarray = numpy.array(particleDataTree)
			mrc.append(partarray, self.filename)
		else:
			f = open(self.filename, "wb+")
			partarray = numpy.array(particleDataTree)
			mrc.write(partarray, f)
			f.close()
			apix = self.apix
			pixeldict = {'x': apix, 'y': apix, 'z': apix, }
			mrc.updateFilePixelSize(self.filename, pixeldict)
	def close(self):
		# close out file
		# write total particles to header, etc.
		return

	################################################
	# Unique functions for this class
	################################################
	def getPixelSize(self):
			pixeldict = mrc.readFilePixelSize(self.filename)
			if pixeldict['x'] == pixeldict['y'] and pixeldict['x'] == pixeldict['z']:
				return pixeldict['x']
			else:
				apDisplay.printWarning("Image Stack has unknown pixel size, using 1.0 A/pixel")
				return 1.0

if __name__ == '__main__':
	import numpy
	# create a random stack of 4 particles with 16x16 dimensions
	a = numpy.random.random((16,16,4))
	# create new stack file
	f1 = MrcClass("temp.mrc")
	# save particles to file
	f1.appendParticlesToFile(a)
	# close stack
	f1.close()
	# open created stack
	f2 = MrcClass("temp.mrc")
	# read particles in stack
	b = f2.readParticles()
	# create new particles from old ones
	a = b*a
	# append and save new particles to stack
	f2.appendParticlesToFile(a)
	# close new stack
	f2.close()

