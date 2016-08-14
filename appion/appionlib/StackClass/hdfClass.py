#!/usr/bin/env python

from pyami import hdf
from appionlib.StackClass import baseClass

####
# This is a low-level file with NO database connections
# Please keep it this way
####

class HdfClass(baseClass.StackClass):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def _getNumberOfParticles(self):
		hdfClass = hdf.HdfFile(self.filename)
		return hdfClass.getNumberOfParticles()
	def _getBoxSize(self):
		hdfClass = hdf.HdfFile(self.filename)
		return hdfClass.getBoxSize()
	def _getPixelSize(self):
		hdfClass = hdf.HdfFile(self.filename)
		return hdfClass.getPixelSize()

	def _readParticlesFromFile(self, particleNumbers):
		"""
		read a list of particles into memory
		particles numbers MUST start at 1
		"""
		offsetParticleNumbers = [(i-1) for i in particleNumbers]
		hdfClass = hdf.HdfFile(self.filename)
		partdatalist = hdfClass.read(offsetParticleNumbers)
		return partdatalist

	def _writeParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and write them to a new file
		or overwrite them to an existing file
		"""
		hdfClass = hdf.HdfFile(self.filename)
		hdfClass.write(particleDataTree)
		return

	def _appendParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and append them to an existing file
		function assumes file already exists
		"""
		hdfClass = hdf.HdfFile(self.filename)
		hdfClass.append(particleDataTree)
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
	f1 = HdfClass("temp.hdf")
	# save particles to file
	f1.appendParticlesToFile(a)
	# close stack
	del f1
	for i in range(10):
		# create a random stack of 4 particles with 16x16 dimensions
		a = numpy.random.random((4,128,128))
		# open created stack
		f2 = HdfClass("temp.hdf")
		# read particles in stack
		b = f2.readParticlesFromFile()
		# create new particles from old ones
		# append and save new particles to stack
		f2.appendParticlesToFile(b[-4:]*a)
		# close new stack
		del f2

