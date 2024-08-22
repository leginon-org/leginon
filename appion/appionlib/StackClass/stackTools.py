#!/usr/bin/env python

import os
import time
import numpy
from pyami import mrc
from pyami import imagefun
from appionlib import apDisplay
from appionlib.StackClass import ProcessStack

####
# This is a low-level file with NO database connections
# Please keep it this way
####

########################################
########################################
########################################
def getNumberOfParticles(filename):
	stackClass = ProcessStack.createStackClass(filename)
	return stackClass.getNumberOfParticles()
########################################
def getBoxSize(filename):
	stackClass = ProcessStack.createStackClass(filename)
	return stackClass.getBoxSize()
########################################
def getPixelSize(filename):
	stackClass = ProcessStack.createStackClass(filename)
	return stackClass.getPixelSize()

########################################
########################################
########################################
def boxParticlesFromFile(mrcfile, stackfile, initboxsize, finalboxsize, coordinates, invert=False):
	"""
	reads mrc and writes a stackfile
	boxsize = integer
	coordinates is 20x2 numpy array
		e.g., coordinates[0] = [2030, 1065]
	"""
	apDisplay.printMsg("Making a stack %s -> %s"%(apDisplay.short(mrcfile), stackfile))
	imgarray = mrc.read(mrcfile)
	boxedparticles = []
	usedparticles = []
	for x,y,partnum in coordinates:
		x1 = x-initboxsize//2
		x2 = x+initboxsize//2
		y1 = y-initboxsize//2
		y2 = y+initboxsize//2
		if x1 < 0 or y1 < 0:
			continue
		if x2 >= imgarray.shape[1] or y2 >= imgarray.shape[0]:
			continue
		initboxpart = imgarray[y1:y2,x1:x2] #numpy arrays are rows,cols --> y,x not x,y
		finalboxpart = imagefun.fourier_scale(initboxpart, finalboxsize)
		if invert is True:
			finalboxpart = -1.0 * finalboxpart
		usedparticles.append(partnum)
		boxedparticles.append(finalboxpart)
	apDisplay.printMsg("Boxed %d of %d particles from %s"
		%(len(boxedparticles), len(coordinates), apDisplay.short(mrcfile)))
	if len(boxedparticles) == 0:
		return None
	stackClass = ProcessStack.createStackClass(stackfile)
	stackClass.appendParticlesToFile(boxedparticles)

	return usedparticles

########################################
########################################
########################################
#===============
def stackStatistics(stackfile, msg=False):
	if msg is True:
		apDisplay.printMsg("merging stack into larger stack")
	stackfile = os.path.abspath(stackfile)

	statStack = StackStatistics(msg)
	statStack.start(stackfile)
	meanlist = statStack.meanlist
	stdevlist = statStack.stdevlist

	return meanlist, stdevlist

#=======================
class StackStatistics(ProcessStack.ProcessStack):
	#===============
	def preLoop(self):
		#override self.partlist to get a subset
		self.meanlist = []
		self.stdevlist = []

	#===============
	def processParticle(self, partarray):
		self.meanlist.append(partarray.mean())
		self.stdevlist.append(partarray.std())

########################################
########################################
########################################
#===============
def mergeStacks(instack="start.hdf", mergestack="combined.mrcs", msg=False):
	if msg is True:
		apDisplay.printMsg("merging stack into larger stack")
	instack = os.path.abspath(instack)
	mergestack = os.path.abspath(mergestack)

	if not os.path.isfile(instack):
		apDisplay.printWarning("could not find input file")
		return False
	if not os.path.isfile(mergestack):
		apDisplay.printWarning("output file does not already exist")
		orignumpart = 0
	else:
		orignumpart = getNumberOfParticles(mergestack)

	mergeStack = MergeStack(msg)
	mergeStack.mergestack = mergestack
	mergeStack.start(instack)

	if not os.path.isfile(mergestack):
		apDisplay.printWarning("output file creation failed")
		return False

	newnumpart = getNumberOfParticles(mergestack)
	innumpart = getNumberOfParticles(instack)
	if orignumpart + innumpart != newnumpart:
		apDisplay.printError("input particles != output partciles")
	return True

#=======================
class MergeStack(ProcessStack.ProcessStack):
	#===============
	def preLoop(self):
		#override self.partlist to get a subset
		self.count = 0
		if self.mergestack is None:
			apDisplay.printWarning("output file not defined")
		self.mergeStackClass = self.StackClassFromFile(self.mergestack)

	#===============
	def processStack(self, stackarray):
		self.mergeStackClass.appendParticlesToFile(stackarray)
		self.index += len(stackarray) #you must have this line in your loop

	#===============
	def postLoop(self):
		return

########################################
########################################
########################################
#===============
def createSubStack(instack="start.hdf", outstack="average.mrcs", partlist=None, msg=False):
	"""
	does not work with IMAGIC, yet
	partlist starts at 1
	"""
	if msg is True:
		apDisplay.printMsg("creating sub-stack from large stack")
	instack = os.path.abspath(instack)
	outstack = os.path.abspath(outstack)

	if not os.path.isfile(instack):
		apDisplay.printWarning("could not find input file")
		return False
	if os.path.isfile(outstack):
		apDisplay.printWarning("output file already exists")
		return False

	subStack = SubStack(msg)
	subStack.outstack = outstack
	subStack.start(instack, partlist)
	if not os.path.isfile(outstack):
		apDisplay.printWarning("output file creation failed")
		return False
	return True

#=======================
class SubStack(ProcessStack.ProcessStack):
	#===============
	def preLoop(self):
		#override self.partlist to get a subset
		self.count = 0
		if self.outstack is None:
			apDisplay.printWarning("output file not defined")
		self.outStackClass = self.StackClassFromFile(self.outstack)

	#===============
	def processStack(self, stackarray):
		self.outStackClass.appendParticlesToFile(stackarray)
		self.index += len(stackarray) #you must have this line in your loop

	#===============
	def postLoop(self):
		return

########################################
########################################
########################################

#===============
def averageStack(stackfile="start.hdf", outfile="average.mrc", partlist=None, msg=False):
	"""
	does not work with IMAGIC, yet
	partlist starts at 1
	"""
	if msg is True:
		apDisplay.printMsg("averaging stack")
	stackfile = os.path.abspath(stackfile)
	if not os.path.isfile(stackfile):
		apDisplay.printWarning("could not create stack average")
		return False
	avgStack = AverageStack(msg)
	avgStack.start(stackfile, partlist)
	if outfile is not None:
		avgmrc = os.path.join(os.path.dirname(stackfile), outfile)
		avgStack.save(avgmrc)
	avgstack = avgStack.getdata()
	return avgstack

#===============
def averageStackList(stacklist, outfile="average.mrc", partlist=None, msg=False):
	"""
	does not work with IMAGIC, yet
	partlist starts at 1
	"""
	if msg is True:
		apDisplay.printMsg("averaging stack list for summary web page")
	if not isinstance(stacklist, list):
		apDisplay.printWarning("could not create stack average, average.mrc")
		return False
	totalsum = 0
	totalindex = 0
	avgStack = AverageStack(msg)
	for stackfile in stacklist:
		stackfile = os.path.abspath(stackfile)
		if not os.path.isfile(stackfile):
			apDisplay.printWarning("could not create stack average, average.mrc")
			continue
		avgStack.start(stackfile)
		totalsum += avgStack.summed
		totalindex += avgStack.index
	average = totalsum / totalindex
	if outfile is not None:
		mrc.write(average, outfile)
	return average

#=======================
class AverageStack(ProcessStack.ProcessStack):
	#===============
	def preLoop(self):
		self.summed = numpy.zeros((self.boxsize,self.boxsize))
		#override self.partlist to get a subset
		self.count = 0

	#===============
	def processStack(self, stackarray):
		if isinstance(stackarray, list):
			stackarray = numpy.array(stackarray)
		self.index += stackarray.shape[0]
		self.summed += stackarray.sum(0)

	#===============
	def save(self, avgfile):
		#normalize
		self.average = self.summed / self.index
		#report
		mean = self.average.mean()
		std = self.average.std()
		if self.msg is True:
			apDisplay.printMsg("mean/std pixel value of average.mrc %.8f +/- %.8f"%(mean, std))
		#save
		mrc.write(self.average, avgfile)

	#===============
	def getdata(self):
		self.average = self.summed / self.index
		mean = self.average.mean()
		std = self.average.std()
		if self.msg is True:
			apDisplay.printMsg("mean/std pixel value of average.mrc %.8f +/- %.8f"%(mean, std))
		return self.average

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
			print("creating huge stack")
			shape = (10,256,256)
			a = numpy.random.random(shape)
			mrc.write(a, stackfile)
			for i in range(1000):
				sys.stderr.write(".")
				a = numpy.random.random(shape)
				mrc.append(a, stackfile)
				time.sleep(0.001)
			print("done")
		averageStack(stackfile, 'average.mrc')
