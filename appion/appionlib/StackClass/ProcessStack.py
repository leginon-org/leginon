#!/usr/bin/env python

import os
import math
import time
from pyami import mem
from appionlib import apDisplay
from appionlib.StackClass import mrcClass
# Issue #4581 disable import until problem solved and module is used for something.
#from appionlib.StackClass import hdfClass
#Neil I moved the import to the HDF read part, so it will only be used when needed
from appionlib.StackClass import imagicClass

####
# This is a low-level file with NO database connections
# Please keep it this way
####

########################################
########################################
########################################
def createStackClass(filename, msg=False):
	extension = os.path.splitext(filename)[-1]
	if extension == '.mrc' or extension == '.mrcs':
		if msg is True: print "MrcClass"
		return mrcClass.MrcClass(filename)
	elif extension == '.hed' or extension == '.img':
		if msg is True: print "ImagicClass"
		return imagicClass.ImagicClass(filename)
	elif extension == '.hdf':
		apDisplay.printError('HdfClass is not imported due to issue #4581')
		if msg is True: print "HdfClass"
		from appionlib.StackClass import hdfClass
		return hdfClass.HdfClass(filename)
	elif extension == '.spi':
		if msg is True: print "SpiderClass"
		raise NotImplementedError
	elif extension == '.png':
		if msg is True: print "PngClass"
		raise NotImplementedError
	elif extension == '.jpg' or extension == '.jpeg':
		if msg is True: print "JpegClass"
		raise NotImplementedError
	raise NotImplementedError("extension does not map to existing stack type %s"%(extension))

########################################
########################################
########################################
class ProcessStack(object):
	"""
	This is class to help process particles in a stack
	that are bigger than the amount of memory on the machine
	"""
	#===============
	def __init__(self, msg=True):
		self.msg = msg
		self.numpart = None
		self.initFunctions()

	#===============
	def message(self, msg):
		if self.msg is True:
			apDisplay.printMsg("ProcessStack2: "+msg)

	#===============
	def StackClassFromFile(self, stackfile):
		return createStackClass(stackfile)

	#===============
	def initValues(self, stackfile, numrequest=None):
		### check for stack
		if not os.path.isfile(stackfile):
			apDisplay.printError("stackfile does not exist: "+stackfile)
		self.stackClass = self.StackClassFromFile(stackfile)

		### amount of free memory on machine (converted to bytes)
		self.freememory = mem.free()*1024
		self.message("Free memory: %s"%(apDisplay.bytes(self.freememory)))
		### box size of particle
		self.boxsize = self.stackClass.getBoxSize()
		self.message("Box size: %d"%(self.boxsize))
		### amount of memory used per particles (4 bytes per pixel)
		self.memperpart = self.boxsize**2 * 4.0
		self.message("Memory used per part: %s"%(apDisplay.bytes(self.memperpart)))
		### maximum number particles that fit into memory
		self.maxpartinmem = self.freememory/self.memperpart
		self.message("Max particles in memory: %d"%(self.maxpartinmem))
		### number particles to fit into memory
		self.partallowed = int(self.maxpartinmem/20.0)
		### FIXME: this severly affect performance and it is probably network dependent
		### at SEMC it is better to have smaller fragments, but this may be different
		if self.partallowed > 1000:
			self.partallowed = 1000 #int(math.sqrt(self.partallowed))
		self.message("Particles allowed in memory: %d"%(self.partallowed))
		### number particles in stack
		numpart = self.stackClass.getNumberOfParticles()
		if self.numpart is None or self.numpart > numpart:
			self.numpart = numpart
		if numrequest is not None and self.numpart > numrequest:
			self.numpart = numrequest
		self.message("Number of particles in stack: %d"%(self.numpart))
		if self.numpart > self.partallowed:
			numchucks = math.ceil(self.numpart/float(self.partallowed))
			self.stepsize = int(self.numpart/numchucks)
		else:
			numchucks = 1
			self.stepsize = self.numpart
		self.message("Particle loop num chunks: %d"%(numchucks))
		self.message("Particle loop step size: %d"%(self.stepsize))

	#===============
	def start(self, stackfile, partlist=None):
		self.stackfile = stackfile
		self.starttime = time.time()
		if partlist is not None:
			partlist.sort()
			numrequest = len(partlist)
		else:
			numrequest = None
		self.initValues(stackfile, numrequest)

		### custom pre-loop command
		self.preLoop()

		first = 1
		last = self.stepsize
		self.index = 0
		t0 = time.time()

		while self.index < self.numpart and first <= self.numpart:
			### print message
			if self.index > 10:
				#self.message("partnum through %d of %d, %s time so far"
				#	%(last, self.numpart, apDisplay.timeString((time.time()-t0))))
				esttime = (time.time()-t0)/float(first)*float(self.numpart-first)
				self.message("partnum %d to %d of %d, %s remain"
					%(first, last, self.numpart, apDisplay.timeString(esttime)))
			else:
				self.message("partnum %d to %d of %d"
					%(first, last, self.numpart))

			### read images
			if partlist is not None:
				stackarray = self.stackClass.readParticlesFromFile(partlist)
			else:
				#self.message("actual partnum %d to %d"%(first-1, last))
				stackarray = self.stackClass.readParticlesFromFile(first=first, last=last)

			### process images
			self.processStack(stackarray)

			### check for proper implementation
			if self.index == 0:
				apDisplay.printError("No particles were processed in stack loop")

			### setup for next iteration
			first = last+1
			last += self.stepsize
			if last > self.numpart:
				last = self.numpart
			### END LOOP

		### check for off-one reading errors
		if self.index < self.numpart-1:
			print "INDEX %d -- NUMPART %d"%(self.index, self.numpart)
			apDisplay.printError("Did not properly process all particles")

		### custom post-loop command
		self.postLoop()

		self.message("finished processing stack in "
			+apDisplay.timeString(time.time()-self.starttime))
		return

	########################################
	# CUSTOMIZED FUNCTIONS
	########################################

	#===============
	def initFunctions(self):
		return

	#===============
	def preLoop(self):
		return

	#===============
	def processStack(self, stackarray):
		for partarray in stackarray:
			self.processParticle(partarray)
			self.index += 1 #you must have this line in your loop
		return

	#===============
	def processParticle(self, partarray):
		raise NotImplementedError

	#===============
	def postLoop(self):
		return
