#!/usr/bin/env python

import os
import math
import time
import numpy
from pyami import mem
from pyami import mrc
from appionlib import apDisplay
from appionlib.StackClass import mrcClass

########################################
########################################
########################################
def createStackClass(filename):
	extension = os.path.splitext(filename)[-1]
	if extension == '.mrc':
		return mrcClass.MrcClass(filename)
	elif extension == '.hed' or extension == '.img':
		return imagicClass.ImagicClass(filename)
	elif extension == '.hdf':
		return hdfClass.HdfClass(filename)
	raise NotImplementedError("extension does not map to existing stack type %s"%(extension))

########################################
########################################
########################################
def numImagesInStack(filename):
	stackClass = createStackClass(filename)
	return stackClass.numpart

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

	#===============
	def message(self, msg):
		if self.msg is True:
			apDisplay.printMsg("processStack: "+msg)

	#===============
	def initValues(self, stackfile, numrequest=None):
		### check for stack
		if not os.path.isfile(stackfile):
			apDisplay.printError("stackfile does not exist: "+stackfile)
		self.stackClass = createStackClass(stackfile)

		### amount of free memory on machine (converted to bytes)
		self.freememory = mem.free()*1024
		self.message("Free memory: %s"%(apDisplay.bytes(self.freememory)))
		### box size of particle
		self.stackClass.readHeader()
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
				esttime = (time.time()-t0)/float(self.index+1)*float(self.numpart-self.index)
				self.message("partnum %d to %d of %d, %s remain"
					%(first, last, self.numpart, apDisplay.timeString(esttime)))
			else:
				self.message("partnum %d to %d of %d"
					%(first, last, self.numpart))

			### read images
			if partlist is None:
				localpartlist = range(first, last+1)
				stackarray = self.stackClass.readParticles(localpartlist)
			else:
				print first, last
				sublist = partlist[first-1:last]
				print sublist
				self.message("actual partnum %d to %d"%(sublist[0], sublist[-1]))
				stackarray = self.stackClass.readParticles(sublist)

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


########################################
########################################
########################################
#===============
def averageStack(stackfile="start.hed", outfile="average.mrc", partlist=None, msg=True):
	"""
	only works with IMAGIC
	
	partlist starts at 1
	"""
	if msg is True:
		apDisplay.printMsg("averaging stack for summary web page")
	stackfile = os.path.abspath(stackfile)
	if not os.path.isfile(stackfile):
		apDisplay.printWarning("could not create stack average, average.mrc")
		return False
	avgStack = AverageStack(msg)
	avgStack.start(stackfile, partlist)
	if outfile is not None:
		avgmrc = os.path.join(os.path.dirname(stackfile), outfile)
		avgStack.save(avgmrc)
	avgstack = avgStack.getdata()
	return avgstack

#=======================
class AverageStack(ProcessStack):
	#===============
	def preLoop(self):
		self.average = numpy.zeros((self.boxsize,self.boxsize))
		#override self.partlist to get a subset
		self.count = 0

	#===============
	def processStack(self, stackarray):
		if isinstance(stackarray, list):
			stackarray = numpy.array(stackarray)
		self.index += stackarray.shape[0]
		self.average += stackarray.sum(0)

	#===============
	def save(self, avgfile):
		mean = self.average.mean() / (self.average.shape[0] * self.average.shape[1])
		print "mean pixel value of average.mrc %.4f"%(mean)
		mrc.write(self.average/self.index, avgfile)

	#===============
	def getdata(self):
		return self.average/self.index

########################################
########################################
########################################
if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		stackfile = sys.argv[1]
		averageStack(stackfile, 'average.mrc')
	else:
		stackfile = 'stackfile.mrc'
		if not os.path.isfile(stackfile):
			print "creating huge stack"
			shape = (10,256,256)
			a = numpy.random.random(shape)
			mrc.write(a, stackfile)
			for i in range(1000):
				sys.stderr.write(".")
				a = numpy.random.random(shape)
				mrc.append(a, stackfile)
				time.sleep(0.001)
			print "done"
		averageStack(stackfile, 'average.mrc')
