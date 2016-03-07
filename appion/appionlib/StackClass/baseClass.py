#!/usr/bin/env python

import os


class StackClass(object):
	################################################
	# Must be implemented in new Stack subClass
	################################################
	def readHeader(self):
		# read the header information
		#  or initialize empty stack
		# required variables to set are below
		self.boxsize = None
		self.apix = None
		self.originalNumberOfParticles = None
		raise NotImplementedError
	def newFile(self):
		# create new file to append to
		raise NotImplementedError
	def readParticles(self, particleNumbers):
		# read a list of particles into memory
		raise NotImplementedError
	def appendParticlesToFile(self, particleDataTree):
		# takes a list of 2D numpy arrays
		#  and wrtie them to a file
		raise NotImplementedError
	def close(self):
		# close out file
		# write total particles to header, etc.
		raise NotImplementedError

	################################################
	# These functions are general should not be copied to subClasses
	################################################
	def __init__(self):
		self.readHeader()
		self.particlesWritten = 0
		self.particlesRead = 0