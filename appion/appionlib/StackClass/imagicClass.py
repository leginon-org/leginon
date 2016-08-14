#!/usr/bin/env python

import os
from appionlib import apImagicFile
from appionlib.StackClass import baseClass

####
# This is a low-level file with NO database connections
# Please keep it this way
####

class ImagicClass(baseClass.StackClass):
	################################################
	# Custom functions
	################################################
	def getHedFile(self):
		root = os.path.splitext(self.filename)[0]
		return root + ".hed"
	def getImgFile(self):
		root = os.path.splitext(self.filename)[0]
		return root + ".hed"

	################################################
	# Must be implemented in new Stack subClass
	################################################
	def _getNumberOfParticles(self):
		headerdict = apImagicFile.readImagicHeader(self.getHedFile())
		return headerdict['nimg']
	def _getBoxSize(self):
		headerdict = apImagicFile.readImagicHeader(self.getHedFile())
		return headerdict['rows']
	def _getPixelSize(self):
		raise NotImplementedError

	def _readParticlesFromFile(self, particleNumbers):
		"""
		read a list of particles numbers into memory
		particles numbers MUST start at 1
		"""
		partdatalist = []
		for partnum in particleNumbers:
			a = apImagicFile.readSingleParticleFromStack(self.filename, partnum=partnum, msg=self.debug)
			partdatalist.append(a)
		return partdatalist

	def _writeParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and write them to a new file
		or overwrite them to an existing file
		"""
		apImagicFile.writeImagic(particleDataTree, self.filename, msg=self.debug)
		return

	def _appendParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and append them to an existing file
		function assumes file already exists
		"""
		apImagicFile.appendParticleListToStackFile(particleDataTree, self.filename, msg=self.debug)
		return

	def _writePixelSizeToFile(self, apix):
		"""
		save a new pixel size to an existing file
		"""
		raise NotImplementedError


if __name__ == '__main__':
	import numpy
	# create a random stack of 4 particles with 16x16 dimensions
	a = numpy.random.random((4,128,128))
	# create new stack file
	f1 = ImagicClass("temp.hed")
	# save particles to file
	f1.appendParticlesToFile(a)
	# close stack
	del f1
	for i in range(10):
		# open created stack
		f2 = ImagicClass("temp.hed")
		# read particles in stack
		b = f2.readParticlesFromFile()
		# create new particles from old ones
		# append and save new particles to stack
		print b[0]
		# create a random stack of 4 particles with 16x16 dimensions
		a = numpy.random.random((4,128,128))
		f2.appendParticlesToFile(b[-4:]*a)
		# close new stack
		del f2

