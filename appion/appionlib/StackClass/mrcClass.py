#!/usr/bin/env python

import os
import numpy
from pyami import mrc
from appionlib import apDisplay
from appionlib.StackClass import baseClass

class MrcClass(baseClass.StackClass):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def readHeader(self):
		"""
		read the header information
		  or initialize new empty stack
		required variables to set are below
		"""
		if os.path.isfile(self.filename) and self.getFileSize() > 1:
			self.mrcheader = mrc.readHeaderFromFile(self.filename)
			self.boxsize = self.mrcheader['nx']
			self.apix = self.getPixelSize()
			self.originalNumberOfParticles = self.mrcheader['nz']
			self.currentParticles = self.mrcheader['nz'] #this number will increment

	def newFile(self):
		"""
		create new file to append to
		"""
		raise NotImplementedError

	def updatePixelSize(self):
		"""
		just update pixel size in file
		"""
		raise NotImplementedError

	def readParticles(self, particleNumbers=None):
		"""
		read a list of particles into memory
		"""
		partdatalist = []
		if particleNumbers is None:
			self.mrcheader = mrc.readHeaderFromFile(self.filename)
			self.currentParticles = self.mrcheader['nz']
			particleNumbers = range(1,self.currentParticles+1)
		for partnum in particleNumbers:
			a = mrc.read(self.filename, zslice=(partnum-1))
			#print partnum, a.shape
			partdatalist.append(a)
		if self.debug is True:
			print "read %d particles"%(len(partdatalist))
		return numpy.array(partdatalist)

	def appendParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays
			* 3D numpy array, shape (numpart, xdim, ydim)
		and wrtie them to a file
		"""
		## always validate
		self.validateParticles(particleDataTree)
		## increment count
		self.currentParticles += len(particleDataTree)
		if os.path.exists(self.filename):
			partarray = numpy.array(particleDataTree)
			mrc.append(partarray, self.filename)
		else:
			f = open(self.filename, "wb+")
			partarray = numpy.array(particleDataTree)
			mrc.write(partarray, f)
			f.close()
			if self.apix is not None:
				pixeldict = {'x': self.apix, 'y': self.apix, 'z': self.apix, }
				mrc.updateFilePixelSize(self.filename, pixeldict)

	def closeOut(self):
		"""
		close out file
		write particle count, pixel size, ... to header, etc.
		mainly for IMAGIC files
		"""
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
	a = numpy.random.random((4,128,128))
	# create new stack file
	f1 = MrcClass("temp.mrc")
	# save particles to file
	f1.appendParticlesToFile(a)
	# close stack
	del f1
	for i in range(10):
		# create a random stack of 4 particles with 16x16 dimensions
		a = numpy.random.random((4,128,128))
		# open created stack
		f2 = MrcClass("temp.mrc")
		# read particles in stack
		b = f2.readParticles()
		# create new particles from old ones
		# append and save new particles to stack
		f2.appendParticlesToFile(b[-4:]*a)
		# close new stack
		del f2

