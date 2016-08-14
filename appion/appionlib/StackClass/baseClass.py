#!/usr/bin/env python

import os
import time
import numpy
from appionlib import apDisplay

####
# This is a low-level file with NO database connections
# Please keep it this way
####

class StackClass(object):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def _getNumberOfParticles(self):
		raise NotImplementedError
	def _getBoxSize(self):
		raise NotImplementedError
	def _getPixelSize(self):
		raise NotImplementedError

	def _readParticlesFromFile(self, particleNumbers):
		"""
		read a list of particles into memory
		particles numbers MUST start at 1
		"""
		raise NotImplementedError
	def _writeParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and write them to a new file
		or overwrite them to an existing file
		"""
		raise NotImplementedError
	def _appendParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and append them to an existing file
		function assumes file already exists
		"""
		raise NotImplementedError
	def _writePixelSizeToFile(self, apix):
		"""
		save a new pixel size to an existing file
		"""
		raise NotImplementedError

	################################################
	# Reporter functions for the base class
	################################################
	def getFileSize(self):
		if not self.fileExists():
			return 0
		return int(os.stat(self.filename)[6])
	def getNumberOfParticles(self):
		if not self.fileExists():
			return 0
		return self._getNumberOfParticles()
	def getBoxSize(self):
		if not self.fileExists():
			return None
		return self._getBoxSize()
	def getPixelSize(self):
		if not self.fileExists():
			return None
		return self._getPixelSize()

	################################################
	# These functions are general should NOT have overrides in subClasses
	################################################
	def __init__(self, filename, debug=True):
		self.filename = filename
		self.debug = debug
		self.particlesWritten = 0
		self.particlesRead = 0
		self.readonly = False
	def fileExists(self):
		if not os.path.exists(self.filename):
			return False
		if int(os.stat(self.filename)[6]) < 128:
			return False
		return True
	def validateParticles(self, particleDataTree):
		firstparticle = particleDataTree[0]
		if firstparticle.shape[0] != firstparticle.shape[1]:
			raise NotImplementedError("Particles are not square")
		if self.boxsize is None:
			self.boxsize = firstparticle.shape[0]
		elif firstparticle.shape[0] != self.boxsize:
			raise ValueError("Particles boxsize different from stack")

	################################################
	# Read / write functions called by apProc2d
	# These functions are general should NOT have overrides in subClasses
	################################################
	def readParticlesFromFile(self, particleNumbers=None):
		"""
		read a list of particles into memory
		"""
		t0 = time.time()
		if particleNumbers is None:
			#set to all particles
			numpart = self.getNumberOfParticles()
			if numpart is None or numpart == 0:
				apDisplay.printWarning("tried to read from empty stack file")
				return []
			particleNumbers = range(1, numpart+1)
		print "going to read %d particles from file"%(len(particleNumbers))
		partdatalist = self._readParticlesFromFile(particleNumbers)
		#convert to numpy array of shape (numpart, box, box)
		partdataarray = numpy.array(partdatalist)
		if self.debug is True:
			apDisplay.printMsg("finished reading %d particles of boxsize %d x %d from file"
				%(partdataarray.shape))
			apDisplay.printMsg("finished writeParticlesToFile() in %s"
				%(apDisplay.timeString(time.time()-t0)))
		return partdataarray

	def writeParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and write them to a new file
		or overwrite them to an existing file
		"""
		t0 = time.time()
		if self.debug is True:
			print "over-writing %d particles to file"%(len(particleDataTree))
		self._writeParticlesToFile(particleDataTree)
		self.particlesWritten += len(particleDataTree)
		if self.debug is True:
			apDisplay.printMsg("finished writeParticlesToFile() in %s"
				%(apDisplay.timeString(time.time()-t0)))

	def appendParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and append them to an existing file
		"""
		t0 = time.time()
		if self.debug is True:
			print "appending %d particles to file"%(len(particleDataTree))
		if not self.fileExists():
			self._writeParticlesToFile(particleDataTree)
		else:
			self._appendParticlesToFile(particleDataTree)
		self.particlesWritten += len(particleDataTree)
		if self.debug is True:
			apDisplay.printMsg("finished appendParticlesToFile() in %s"
				%(apDisplay.timeString(time.time()-t0)))

	def writePixelSizeToFile(self, apix):
		"""
		save a new pixel size to an existing file
		"""
		if apix is None:
			raise ValueError("apix not defined")
		if self.debug is True:
			print "writing pixel size %.4f Angstroms to file"%(apix)
		self._writePixelSizeToFile(apix)

