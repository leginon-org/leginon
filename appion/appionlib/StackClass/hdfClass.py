#!/usr/bin/env python

import os
from pyami import hdf
from appionlib import apDisplay
from appionlib.StackClass import baseClass

class HdfClass(baseClass.StackClass):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def readHeader(self):
		"""
		read the header information
		  or initialize new empty stack
		required variables to set are below
		"""
		if os.path.isfile(self.filename) and self.getFileSize() > 10:
			self.hdfClass = hdf.HdfFile(self.filename)
			self.apix = self.hdfClass.getPixelSize()
			self.boxsize = self.hdfClass.getBoxSize()
			self.originalNumberOfParticles = self.hdfClass.numpart
			self.currentParticles = self.hdfClass.numpart #this number will increment

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
		self.apix = self.hdfClass.getPixelSize()
		self.boxsize = self.hdfClass.getBoxSize()
		self.currentParticles = self.hdfClass.numpart
		partdatalist = self.hdfClass.read(particleNumbers)
		return partdatalist

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
		if os.path.isfile(self.filename) and self.getFileSize() > 10:
			self.hdfClass.append(particleDataTree)
		else:
			self.hdfClass = hdf.HdfFile(self.filename)
			#self.hdfClass.apix = self.apix
			self.hdfClass.write(particleDataTree)

	def closeOut(self):
		"""
		close out file
		write particle count, pixel size, ... to header, etc.
		mainly for IMAGIC files
		"""
		return

if __name__ == '__main__':
	import numpy
	# create a random stack of 4 particles with 16x16 dimensions
	a = numpy.random.random((4,16,16))
	# create new stack file

	f1 = HdfClass("temp.hdf")
	# save particles to file
	f1.appendParticlesToFile(a)
	# close stack
	del f1
	# open created stack
	f2 = HdfClass("temp.hdf")
	# read particles in stack
	b = f2.readParticles()
	# create new particles from old ones
	a = b*a
	# append and save new particles to stack
	f2.appendParticlesToFile(a)
	# close new stack
	del f2

