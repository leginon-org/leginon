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
		return root + ".img"

	################################################
	# Override functions
	################################################
	def removeStack(self, warn=True):
		"""
		delete file, mostly for IMAGIC to override
		"""
		self._removeStack(self.getHedFile(), warn)
		self._removeStack(self.getImgFile(), warn)

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

	def _readParticleListFromFile(self, particleNumbers):
		"""
		read a list of particles numbers into memory
		particles numbers MUST start at 1
		"""
		partdatalist = []
		for partnum in particleNumbers:
			a = apImagicFile.readSingleParticleFromStack(self.filename, partnum=partnum, msg=self.debug)
			partdatalist.append(a)
		return partdatalist

	def _readParticleChunkFromFile(self, first, last):
		"""
		read a fixed range of particles into memory
		particles numbers MUST start at 1
		"""
		if self.headerdict is None:
			self.headerdict = apImagicFile.readImagicHeader(self.getHedFile())
		numpart = last - first + 1
		images = apImagicFile.readImagicData(self.getImgFile(), self.headerdict, first, numpart)
		return images

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

