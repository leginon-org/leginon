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
		numpart = header.get('mz')
		if numpart is None:
			numpart = header.get('nz')
		return numpart
	def _getBoxSize(self):
		header = mrc.read_file_header(self.filename)
		return header['nx']
	def _getPixelSize(self):
		pixeldict = mrc.readFilePixelSize(self.filename)
		return pixeldict['x']

	def _readParticleListFromFile(self, particleNumbers):
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


