#!/usr/bin/env python

import numpy
from pyami import mrc
from appionlib.StackClass import baseClass

####
# This is a low-level file with NO database connections
# Please keep it this way
####

class MrcClass(baseClass.StackClass):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def _getNumberOfParticles(self):
		header = mrc.read_file_header(self.filename)
		return header['nz']
	def _getBoxSize(self):
		header = mrc.read_file_header(self.filename)
		return header['nx']
	def _getPixelSize(self):
		pixeldict = mrc.readFilePixelSize(self.filename)
		return pixeldict['x']

	def _readParticlesFromFile(self, particleNumbers):
		"""
		read a list of particles into memory
		particles numbers MUST start at 1
		"""
		partdatalist = []
		for partnum in particleNumbers:
			a = mrc.read(self.filename, zslice=(partnum-1))
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
		partarray = numpy.array(particleDataTree)
		mrc.write(partarray, self.filename)
		return

	def _appendParticlesToFile(self, particleDataTree):
		"""
		input:
			* list of 2D numpy arrays [(x,y), (x,y), ...]
			* 3D numpy array, shape (numpart, xdim, ydim)
		and append them to an existing file
		function assumes file already exists
		"""
		partarray = numpy.array(particleDataTree)
		mrc.append(partarray, self.filename)
		return

	def _writePixelSizeToFile(self, apix):
		"""
		save a new pixel size to an existing file
		"""
		pixeldict = {'x': apix, 'y': apix, 'z': apix, }
		mrc.updateFilePixelSize(self.filename, pixeldict)
		return


if __name__ == '__main__':
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
		b = f2.readParticlesFromFile()
		# create new particles from old ones
		# append and save new particles to stack
		f2.appendParticlesToFile(b[-4:]*a)
		# close new stack
		del f2

