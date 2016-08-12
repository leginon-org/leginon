#!/usr/bin/env python

import os
import numpy
from appionlib import apDisplay
from appionlib import apImagicFile
from appionlib.StackClass import baseClass

####
# This is a low-level file with NO database connections
# Please keep it this way
####

class ImagicClass(baseClass.StackClass):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def readHeader(self):
		"""
		run during __init__ phase
		read the header information
		  or initialize new empty stack
		required variables to set are below
		"""
		root = os.path.splitext(self.filename)[0]
		self.hedfile = root + ".hed"
		self.imgfile = root + ".img"
		if os.path.isfile(self.hedfile) and self.getFileSize() > 10:
			headerdict = apImagicFile.readImagicHeader(self.hedfile)
			self.boxsize = headerdict['rows']
			self.originalNumberOfParticles = headerdict['nimg']
			self.currentParticles = headerdict['nimg'] #this number will increment

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
			headerdict = apImagicFile.readImagicHeader(self.hedfile)
			self.currentParticles = headerdict['nimg']
			particleNumbers = range(1,self.currentParticles+1)
		for partnum in particleNumbers:
			a = apImagicFile.readSingleParticleFromStack(self.filename, partnum=partnum, msg=self.msg)
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
		if os.path.isfile(self.filename) and self.getFileSize() > 10:
			apImagicFile.appendParticleListToStackFile(particleDataTree, self.filename, msg=self.msg)
		else:
			apImagicFile.writeImagic(particleDataTree, self.filename, msg=self.msg)
		return

	def closeOut(self):
		"""
		close out file
		write particle count, pixel size, ... to header, etc.
		mainly for IMAGIC files
		"""
		apImagicFile.numberStackFile(self.hedfile)
		return

	def getPixelSize(self):
		return self.apix


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
		b = f2.readParticles()
		# create new particles from old ones
		# append and save new particles to stack
		print b[0]
		# create a random stack of 4 particles with 16x16 dimensions
		a = numpy.random.random((4,128,128))
		f2.appendParticlesToFile(b[-4:]*a)
		# close new stack
		del f2

