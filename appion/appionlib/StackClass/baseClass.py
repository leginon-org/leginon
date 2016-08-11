#!/usr/bin/env python

import os

class StackClass(object):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def readHeader(self):
		"""
		read the header information
		  or initialize new empty stack
		required variables to set are below
		"""
		self.boxsize = None
		self.apix = None
		self.originalNumberOfParticles = None
		raise NotImplementedError
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
		raise NotImplementedError
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
		raise NotImplementedError
	def closeOut(self):
		"""
		close out file
		write particle count, pixel size, ... to header, etc.
		mainly for IMAGIC files
		"""
		raise NotImplementedError

	################################################
	# These functions are general should not be copied to subClasses
	################################################
	def __init__(self, filename):
		self.filename = filename
		self.readHeader()
		self.particlesWritten = 0
		self.particlesRead = 0
		self.boxsize = None
		self.apix = 1.0 # assume 1.0 apix unless specified
		self.originalNumberOfParticles = 0
		self.currentParticles = 0
		self.readonly = False
	def setPixelSize(self, apix):
		self.apix = apix
	def validateParticles(self, particleDataTree):
		firstparticle = particleDataTree[0]
		if firstparticle.shape[0] != firstparticle.shape[1]:
			raise NotImplementedError("Particles are not square")
		if self.boxsize is None:
			self.boxsize = firstparticle.shape[0]
		elif firstparticle.shape[0] != self.boxsize:
			raise ValueError("Particles boxsize different from stack")

	################################################
	# Reporter functions for this class
	################################################
	def getFileSize(self):
		return int(os.stat(self.filename)[6])
	def getNumberOfParticles(self):
		return self.currentParticles
	def getBoxSize(self):
		return self.boxsize
	def getPixelSize(self):
		return self.apix

	################################################
	# Unique functions for this class
	################################################

if __name__ == '__main__':
	import numpy
	# create a random stack of 4 particles with 16x16 dimensions
	a = numpy.random.random((16,16,4))
	# create new stack file
	f1 = StackClass("temp.mrc")
	# set the pixel size
	f1.setPixelSize(1.0)
	# save particles to file
	f1.appendParticlesToFile(a)
	# close stack
	f1.close()
	# open created stack
	f2 = StackClass("temp.mrc")
	# read particles in stack
	b = f2.readParticles()
	# create new particles from old ones
	a = b*a
	# append and save new particles to stack
	f2.appendParticlesToFile(a)
	# close new stack
	f2.close()

